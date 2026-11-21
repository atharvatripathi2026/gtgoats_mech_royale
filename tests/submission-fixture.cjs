const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {randomUUID} = require('node:crypto');

const directory = path.join(__dirname, '..', 'submission-helper');
const repository = 'https://github.com/atharvatripathi2026/gtgoats_mech_royale';
const queueUrl = 'https://raw.githubusercontent.com/atharvatripathi2026/gtgoats_mech_royale/practice-queue/queue.json';
const track = 'https://www.joinbuilders.org/buildathon/tracks/builders';
const hour = 3_600_000;
const cutoff = Date.parse('2026-11-22T16:00:00Z');
const candidates = Array.from({length: 7}, (_, i) => ({commit: String(i + 1).repeat(40)}));

function harness() {
    const disk = {};
    const http = [];
    const sender = {id:'fixture-extension', frameId:0, tab:{id:1,url:track}, url:track};
    const env = {now:cutoff - 8*hour, queue:{version:1, repository, candidates}, sender, http};
    env.reboot = () => {
        let receive;
        const event = () => ({addListener() {}});
        class Clock extends Date {
            constructor(...args) { super(...(args.length ? args : [env.now])); }
            static now() { return env.now; }
        }
        const chrome = {
            runtime:{id:sender.id, onMessage:{addListener(fn) { receive = fn; }}, onInstalled:event(), onStartup:event()},
            alarms:{onAlarm:event(), async create() {}, async clear() {}},
            tabs:{async query() {return [];}, async sendMessage() {}, onUpdated:event()},
            storage:{local:{
                async get(key) {
                    if (typeof key === 'string') return key in disk ? {[key]:structuredClone(disk[key])} : {};
                    return structuredClone(disk);
                },
                async set(values) { Object.assign(disk, structuredClone(values)); },
            }},
        };
        async function fetch(url, options) {
            http.push({url:String(url), options});
            assert.equal(String(url), queueUrl);
            assert.equal(options.credentials, 'omit');
            return {ok:true,status:200,json:async()=>structuredClone(env.queue),
                    text:async()=>JSON.stringify(env.queue),headers:new Headers()};
        }
        vm.runInNewContext(readFileSync(path.join(directory,'worker.js'),'utf8'),
            {chrome, Date:Clock, fetch, crypto:{randomUUID}, URL, setTimeout, clearTimeout,
             AbortController, AbortSignal, structuredClone, console});
        assert.equal(typeof receive, 'function');
        env.message = async (message, source=sender) => {
            let respond;
            const done = new Promise(resolve => { respond = resolve; });
            const result = receive(message,source,respond);
            if (result instanceof Promise || result && typeof result.then === 'function') return await result;
            if (result !== true) return await Promise.race([done, Promise.resolve(null)]);
            return await done;
        };
    };
    env.reboot();
    return env;
}
function visible(extra={}) {
    return {historyReady:true, team:'GT Goats', identityVerified:true, queued:false, remaining:4,
            commits:['4cb4a9ea753e'], receipts:[{commit:'4cb4a9ea753e',receipt:'BB-073A1E2D',status:'Scored'}], ...extra};
}
function start(worker, sender=worker.sender) {
    return worker.message({type:'start', team:'GT Goats', attested:true, view:visible()}, sender);
}
async function reserve(worker, view=visible(), sender=worker.sender) {
    return worker.message({type:'claim',view},sender);
}
async function dispatch(worker, lease, view=visible(), sender=worker.sender) {
    return worker.message({type:'dispatch',token:lease.token,view},sender);
}

module.exports = {candidates, cutoff, directory, dispatch, harness, hour, repository, reserve, start, track, visible};
