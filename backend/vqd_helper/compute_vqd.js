const { JSDOM } = require("jsdom");
const crypto = require("crypto");

let input = "";
process.stdin.on("data", chunk => input += chunk);
process.stdin.on("end", async () => {
  try {
    const { base64Hash, userAgent } = JSON.parse(input);
    const ua = userAgent || "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36";
    const jsScript = Buffer.from(base64Hash, "base64").toString("utf-8");
    const dom = new JSDOM(
      `<!DOCTYPE html><html><head></head><body></body></html>`,
      { runScripts: "dangerously", userAgent: ua }
    );
    dom.window.top.__DDG_BE_VERSION__ = 1;
    dom.window.top.__DDG_FE_CHAT_HASH__ = 1;
    const result = await dom.window.eval(jsScript);
    result.client_hashes[0] = ua;
    result.client_hashes = result.client_hashes.map(t => crypto.createHash("sha256").update(t).digest("base64"));
    console.log(Buffer.from(JSON.stringify(result)).toString("base64"));
  } catch (err) {
    console.error(JSON.stringify({ error: err.message }));
    process.exit(1);
  }
});
