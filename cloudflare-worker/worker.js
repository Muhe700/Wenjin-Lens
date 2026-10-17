/**
 * ============================================================================
 * 文津·选刊助手 (Wenjin-Lens) — Cloudflare Worker 反向代理脚本
 * 作用：将国内服务器对 Google Gemini API 的请求无缝反代至官方接口
 * ============================================================================
 */

export default {
  async fetch(request, env, ctx) {
    // 处理预检请求 (CORS OPTIONS)
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "*",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    const url = new URL(request.url);

    // 将请求转发至 Google 官方 Gemini 端点
    url.hostname = "generativelanguage.googleapis.com";
    url.port = "443";
    url.protocol = "https:";

    // 克隆请求头并修正 Host
    const newHeaders = new Headers(request.headers);
    newHeaders.set("Host", "generativelanguage.googleapis.com");

    const newRequest = new Request(url.toString(), {
      method: request.method,
      headers: newHeaders,
      body: request.body,
      redirect: "follow",
    });

    try {
      const response = await fetch(newRequest);

      // 附加跨域响应头
      const newResponseHeaders = new Headers(response.headers);
      newResponseHeaders.set("Access-Control-Allow-Origin", "*");
      newResponseHeaders.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
      newResponseHeaders.set("Access-Control-Allow-Headers", "*");

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newResponseHeaders,
      });
    } catch (err) {
      return new Response(
        JSON.stringify({
          error: "Cloudflare 反代节点转发失败",
          detail: err.message,
        }),
        {
          status: 502,
          headers: {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
    }
  },
};
