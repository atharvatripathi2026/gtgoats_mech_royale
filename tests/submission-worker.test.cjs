const assert = require('node:assert/strict');
const test = require('node:test');
const {candidates, cutoff, dispatch, harness, hour, repository, reserve, start, track, visible} = require('./submission-fixture.cjs');

test('restricts tab origin, manifest repository and signed-in history before claiming', async () => {
    const w = harness();
    for (const sender of [
        {...w.sender,url:'https://example.com/buildathon/tracks/builders'},
        {...w.sender,frameId:1},
    ]) assert.ok(!(await start(w,sender))?.ok);
    assert.ok(!(await reserve(w)).ok);
    assert.ok((await start(w)).ok);
    for (const view of [
        visible({historyReady:false}), visible({identityVerified:false}),
        visible({queued:true}), visible({remaining:0}),
    ]) assert.ok(!(await reserve(w,view)).ok);
    w.queue = {...w.queue, repository:'https://github.com/another-team/their-bot'};
    assert.ok(!(await reserve(w)).ok);
    assert.ok(w.http.length > 0);
});

test('one tab owns a lease; a failed pre-click check can release without spending', async () => {
    const w = harness();
    await start(w);
    const second = {...w.sender,tab:{id:2,url:track}};
    const leases = await Promise.all([reserve(w),reserve(w,visible(),second)]);
    assert.equal(leases.filter(l=>l.ok).length,1);
    const index = leases.findIndex(l=>l.ok), first=leases[index];
    const owner = index === 0 ? w.sender : second;
    const other = index === 0 ? second : w.sender;
    assert.equal(first.repository,repository);
    assert.equal(first.commit,candidates[0].commit);
    assert.ok(!(await dispatch(w,first,visible(),other)).ok);
    assert.ok(!(await dispatch(w,first,visible({queued:true}),owner)).ok);
    await w.message({type:'release',token:first.token},owner);
    const next = await reserve(w,visible(),other);
    assert.ok(next.ok);
    assert.equal(next.commit,first.commit);
});

test('an unconfirmed click survives restart and blocks duplicate submissions', async () => {
    const w = harness();
    await start(w);
    const first = await reserve(w);
    assert.ok(first.ok);
    assert.ok((await dispatch(w,first)).ok);
    await w.message({type:'uncertain',token:first.token});
    w.now += hour + 5000;
    w.reboot();
    assert.ok(!(await reserve(w)).ok);
    const listed = visible({commits:['4cb4a9e',first.commit.slice(0,12)],queued:true});
    assert.ok(!(await reserve(w, listed)).ok);
    const next = await reserve(w,{...listed,queued:false});
    assert.ok(next.ok);
    assert.equal(next.commit,candidates[1].commit);
});

test('honors the site quota, stored attempts and competition cutoff', async () => {
    const w = harness();
    await start(w);
    const history = ['4cb4a9e'];
    const began = w.now;
    for (let i=0;i<4;i++) {
        w.now = began+i*(hour/4+1001);
        const view = visible({commits:[...history]});
        const lease = await reserve(w,view);
        assert.ok(lease.ok,JSON.stringify(lease));
        assert.equal(lease.commit,candidates[i].commit);
        assert.ok((await dispatch(w,lease,view)).ok);
        history.push(lease.commit.slice(0,12));
        await w.message({type:'complete',token:lease.token,view:visible({commits:[...history]})});
        assert.ok(!(await reserve(w,visible({commits:[...history]}))).ok);
    }
    w.now = began+hour-1;
    w.reboot();
    assert.ok(!(await reserve(w,visible({commits:[...history]}))).ok);
    w.now = began+hour+10000;
    assert.ok(!(await reserve(w,visible({commits:[...history],remaining:0}))).ok);
    const lease = await reserve(w,visible({commits:[...history]}));
    assert.ok(lease.ok);
    w.now = cutoff;
    assert.ok(!(await dispatch(w,lease,visible({commits:[...history]}))).ok);
    w.reboot();
    assert.ok(!(await reserve(w,visible({commits:[...history]}))).ok);
});

test('a stopped helper and a changed public queue invalidate unspent authorizations', async () => {
    const w = harness();
    await start(w);
    const withdrawn = await reserve(w);
    assert.ok(withdrawn.ok);
    w.queue = {...w.queue, candidates:candidates.slice(1)};
    assert.ok(!(await dispatch(w,withdrawn)).ok);
    const current = await reserve(w);
    assert.ok(current.ok);
    assert.equal(current.commit,candidates[1].commit);
    await w.message({type:'stop'});
    w.reboot();
    assert.ok(!(await dispatch(w,current)).ok);
    assert.ok(!(await reserve(w)).ok);
    await start(w);
    assert.ok(!(await dispatch(w,current)).ok);
});

test('an unknown initial quota waits; an expired unspent lease cannot dispatch', async () => {
    const w = harness();
    await start(w);
    assert.ok(!(await reserve(w,visible({remaining:null}))).ok);
    const first = await reserve(w);
    assert.ok(first.ok);
    w.now += 61_000;
    assert.ok(!(await dispatch(w,first)).ok);
    const replacement = await reserve(w);
    assert.ok(replacement.ok);
    assert.equal(replacement.commit,first.commit);
    assert.notEqual(replacement.token,first.token);
});

test('manual retirement requires a stopped verified view and never retries the ambiguous SHA', async () => {
    const w = harness();
    await start(w);
    const first = await reserve(w);
    await dispatch(w,first);
    await w.message({type:'uncertain',token:first.token});
    const retire = view=>w.message({type:'resolve',team:'GT Goats',attested:true,commit:first.commit,view});
    assert.ok(!(await retire(visible())).ok);
    await w.message({type:'stop'});
    assert.ok(!(await retire(visible({queued:true}))).ok);
    assert.ok(!(await retire(visible({identityVerified:false}))).ok);
    assert.ok((await retire(visible())).ok);
    w.reboot();
    await start(w);
    assert.ok(!(await reserve(w)).ok);
    w.now += hour+1001;
    assert.equal((await reserve(w)).commit,candidates[1].commit);
});

test('result-based ranking prefers a scored parent and retains an issued lease', async () => {
    const w = harness();
    const a = '4cb4a9ea753e8df3744a9ba8d44053068e64e535';
    const b = '9e59bbfd46f562dbb88d0a4377dc333ce2f8c273';
    const scored = (first,second)=>visible({commits:[a.slice(0,12),b.slice(0,12)],receipts:[
        {receipt:'BB-073A1E2D',commit:a.slice(0,12),status:'Scored',score:first,message:'First'},
        {receipt:'BB-C6067CA3',commit:b.slice(0,12),status:'Scored',score:second,message:'Second'},
    ]});
    w.queue = {...w.queue,candidates:[
        {commit:candidates[0].commit,parents:[a]}, {commit:candidates[1].commit,parents:[b]},
    ]};
    await start(w);
    const lease = await reserve(w,scored(3,8));
    assert.equal(lease.commit,candidates[1].commit);
    w.queue.candidates.unshift({commit:candidates[2].commit,parents:[a]});
    const grant = await dispatch(w,lease,scored(10,8));
    assert.ok(grant.ok,JSON.stringify(grant));
    assert.equal(grant.commit,lease.commit);
    w.reboot();
    const data = await w.message({type:'export',view:scored(10,8)});
    assert.equal(data.results.find(x=>x.receipt==='BB-073A1E2D').score,10);
    assert.equal(data.results.find(x=>x.receipt==='BB-C6067CA3').message,'Second');
});

test('every fourth slot tries the oldest queued candidate', async () => {
    const w = harness();
    const parent='4cb4a9ea753e8df3744a9ba8d44053068e64e535';
    w.queue = {...w.queue,candidates:candidates.map((c,i)=> i ? {...c,parents:[parent]} : c)};
    await start(w);
    const history=visible().commits;
    for (const index of [1,2,3,0]) {
        const view=visible({commits:[...history]});
        const grant=await reserve(w,view);
        assert.equal(grant.commit,candidates[index].commit);
        await dispatch(w,grant,view);
        history.push(grant.commit.slice(0,12));
        await w.message({type:'complete',token:grant.token,view:visible({commits:[...history]})});
        w.now += hour/4+1001;
    }
});
