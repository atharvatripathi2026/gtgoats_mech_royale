/* Local fixture only. Requires Playwright and Chromium (set CHROMIUM_BIN for a custom executable). */
const assert = require('node:assert/strict');
const {existsSync} = require('node:fs');
const path = require('node:path');
const {test, before, after} = require('node:test');
const {chromium} = require('playwright');
const {candidates, directory, harness, repository, track} = require('./submission-fixture.cjs');

const knownSha = '4cb4a9ea753e', knownReceipt = 'BB-073A1E2D';
function card({sha=knownSha, receipt=knownReceipt, status='Scored', repo=repository, score='3.60', message='Official fixture result'}={}) {
    return `<li><div><span>${receipt}</span><span>${status}</span><span>${score}</span><span>Nov 21</span></div>
        <p>${repo} @ ${sha}</p><p class="break-words whitespace-pre-wrap">${message}</p>
        <button type="button" onclick="window.finalClicks++">Pick as our final entry</button></li>`;
}
function submissionPage({rows=card(),remaining=4,signedIn=true}={}) {
    return `<!doctype html><html lang="en"><head><title>Builders - Mech Royale</title></head><body>
      <main><h1>Builders - Mech Royale</h1>
      <section aria-label="Your hour and the queue"><p>${remaining} of 4 left this hour</p></section>
      <div id="submit">${signedIn ? `
        <form><h3>Submit</h3><label>Public GitHub repository <input name="repo" type="url" required></label>
          <label>Commit (optional) <input name="commit" type="text"></label>
          <span>${remaining} of 4 left this hour</span><button>Submit</button></form>
        <section><h3>Your team's submissions</h3><ol>${rows}</ol></section>` : 'Sign in to submit.'}</div>
      </main></body></html>`;
}
let browser;
before(async () => {
    const bin = process.env.CHROMIUM_BIN || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
    browser = await chromium.launch({executablePath:bin, headless:true, args:['--host-resolver-rules=MAP * ~NOTFOUND']});
});
after(async () => { if (browser) await browser.close(); });

async function fixture(t, markup, {onMessage, onSubmit='receipt', worker=harness()}={}) {
    const context = await browser.newContext();
    t.after(()=>context.close());
    const page = await context.newPage();
    const requests = [];
    await page.route('**/*', route => {
        if (route.request().url() === track) {
            return route.fulfill({status:200,contentType:'text/html',body:markup});
        }
        return route.abort();
    });
    await page.exposeFunction('callWorker', async message => {
        requests.push(message);
        if (onMessage) await onMessage(message,page);
        return await worker.message(message);
    });
    await page.addInitScript(() => {
        window.requestsSent = [];
        window.finalClicks = 0;
        const wake = [];
        window.chrome = window.chrome || {};
        window.chrome.runtime = {
            id:'fixture-extension',
            sendMessage(message, callback) {
                const result = window.callWorker(message);
                if (callback) result.then(callback);
                return result;
            },
            onMessage:{addListener(fn) {wake.push(fn);}},
        };
        window.fixtureWake = () => Promise.all(wake.map(fn=>fn({type:'wake'})));
    });
    async function loadPage() {
      await page.clock.setFixedTime(new Date(worker.now));
      await page.evaluate(({onSubmit}) => {
        document.querySelector('form')?.addEventListener('submit', (event) => {
            event.preventDefault();
            const values = Object.fromEntries(new FormData(event.target));
            window.requestsSent.push(values);
            if (onSubmit === 'receipt') {
                const li = document.createElement('li');
                li.innerHTML = '<div><span>BB-A1111111</span><span>Queued</span></div><p></p>';
                li.querySelector('p').textContent = values.repo + ' @ ' + values.commit.slice(0,12);
                document.querySelector('#submit ol').prepend(li);
            }
        });
    }, {onSubmit});
      await page.addScriptTag({path:path.join(directory,'content.js')});
    }
    await page.goto(track);
    await loadPage();
    async function reload() { await page.reload(); await loadPage(); }
    return {worker,page,requests,reload};
}

test('one explicit start submits the approved practice SHA; final selection stays untouched', async t => {
    const {page,requests} = await fixture(t,submissionPage());
    const start = page.getByRole('button',{name:'Start GT Goats submissions',exact:true});
    await start.waitFor({timeout:3000});
    assert.deepEqual(await page.evaluate(()=>window.requestsSent),[]);
    await start.click();
    await page.waitForFunction(()=>window.requestsSent.length === 1,null,{timeout:5000});
    assert.deepEqual(await page.evaluate(()=>window.requestsSent),[{repo:repository,commit:candidates[0].commit}]);
    assert.equal(await page.evaluate(()=>window.finalClicks),0);
    assert.ok(requests.some(m=>m.type==='dispatch'));
});

test('a foreign team receipt, mismatched repository, or signed-out view never submits', async t => {
    for (const options of [
        {rows:card({receipt:'BB-A0000000'})},
        {rows:card({repo:'https://github.com/another-team/their-bot'})},
        {signedIn:false},
    ]) {
        const {page,requests} = await fixture(t,submissionPage(options));
        const start = page.getByRole('button',{name:'Start GT Goats submissions',exact:true});
        // Some inaccessible states omit the toolbar entirely; others expose a disabled control.
        if (await start.count() && await start.isEnabled()) await start.click();
        assert.deepEqual(await page.evaluate(()=>window.requestsSent),[]);
        assert.ok(!requests.some(m=>m.type==='dispatch'));
        assert.equal(await page.evaluate(()=>window.finalClicks),0);
    }
});

test('a changed form between authorization and click stays unsubmitted', async t => {
    const {page} = await fixture(t,submissionPage(),{
        onMessage:async (msg, p) => {
            if (msg.type === 'dispatch') await p.evaluate(()=>document.querySelector('form button').disabled=true);
        },
    });
    await page.getByRole('button',{name:'Start GT Goats submissions'}).click();
    await page.getByRole('status').filter({hasText:/reservation changed|checking team history/i}).waitFor({timeout:3000});
    assert.deepEqual(await page.evaluate(()=>window.requestsSent),[]);
    assert.equal(await page.evaluate(()=>window.finalClicks),0);
});

test('page reload and a worker restart preserve a missing receipt; a later rejection resolves it', async t => {
    const {page,worker,reload} = await fixture(t,submissionPage(),{onSubmit:'unknown'});
    await page.getByRole('button',{name:'Start GT Goats submissions'}).click();
    await page.waitForFunction(()=>window.requestsSent.length === 1,null,{timeout:4000});
    worker.now += 3_600_001;
    worker.reboot();
    await reload();
    await page.getByRole('status').filter({hasText:/previous commit|confirmation|receipt/i}).waitFor({timeout:3000});
    assert.deepEqual(await page.evaluate(()=>window.requestsSent),[]);
    await page.evaluate(({repo,sha}) => {
        const li=document.createElement('li');
        li.innerHTML='<div><span>BB-B2222222</span><span>Rejected</span></div><p></p><p>Image did not build</p>';
        li.querySelector('p').textContent=repo+' @ '+sha.slice(0,12);
        document.querySelector('#submit ol').prepend(li);
        window.fixtureWake();
    }, {repo:repository,sha:candidates[0].commit});
    await page.waitForFunction(()=>window.requestsSent.length === 1,null,{timeout:4000});
    assert.equal((await page.evaluate(()=>window.requestsSent))[0].commit,candidates[1].commit);
    assert.equal(await page.evaluate(()=>window.finalClicks),0);
});

test('a stopped team can export visible feedback without sending a practice entry', async t => {
    const {page,requests} = await fixture(t,submissionPage({rows:card({message:'Result: good, steady'})}));
    await page.getByRole('button',{name:'Export results'}).waitFor();
    for (const format of ['JSON','CSV']) {
        await page.getByLabel('Result format').selectOption({label:format});
        const event = page.waitForEvent('download',{timeout:3000});
        await page.getByRole('button',{name:'Export results'}).click();
        const download = await event;
        const stream = await download.createReadStream();
        const chunks = [];
        for await (const chunk of stream) chunks.push(chunk);
        const text = Buffer.concat(chunks).toString();
        if (format === 'JSON') {
            const data = JSON.parse(text);
            const item = data.results.find(r=>r.receipt===knownReceipt);
            assert.equal(item.score,3.6);
            assert.equal(item.message,'Result: good, steady');
        } else {
            assert.match(text,/BB-073A1E2D/);
            assert.match(text,/"Result: good, steady"/);
        }
    }
    assert.equal(requests.some(m=>m.type==='dispatch'),false);
    assert.equal(await page.evaluate(()=>window.finalClicks),0);
});

test('a pre-existing draft for a different repository stays intact', async t => {
    const {page,requests} = await fixture(t,submissionPage());
    const draft = 'https://github.com/another-team/unfinished-draft';
    await page.locator('input[name=repo]').fill(draft);
    await page.getByRole('button',{name:'Start GT Goats submissions'}).click();
    await page.getByRole('status').filter({hasText:/eligible practice form|current draft/i}).waitFor({timeout:3000});
    assert.equal(await page.locator('input[name=repo]').inputValue(),draft);
    assert.deepEqual(await page.evaluate(()=>window.requestsSent),[]);
    assert.equal(requests.some(m=>m.type==='dispatch'),false);
});
