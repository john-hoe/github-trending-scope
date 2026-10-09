#!/bin/bash
# 在 Mac 上运行：把当前站点以「draft」预览分支部署到 Cloudflare Pages（带密码、noindex），视频传到 R2 的 draft/<token>/ 下。
# 不动正式站（正式分支是 main）、不改 DNS。首次运行生成 token+密码，存在 ~/claude-work/scope-draft/.secret（600，不进仓库）。
# 用法: bash tools/draft-deploy.sh [--skip-upload] [--only=<日期>]
#   --only=2026-10-09 只上传该日期目录下的视频（已传过的日期不用重传）；SITE_DIR=<目录> 指定要构建的仓库副本。
set -e
export PATH=/opt/homebrew/bin:$PATH
S=${SITE_DIR:-~/claude-work/scope-site}; ST=~/claude-work/scope-draft; M=~/claude-work/scope-media/v
SKIP=0; ONLY=""; ROTATE=0
for a in "$@"; do case $a in --skip-upload) SKIP=1;; --only=*) ONLY=${a#--only=};; --rotate) ROTATE=1;; esac; done
#   --rotate 换一个新的视频路径 token（视频内容改过、又怕 Cloudflare 边缘缓存还给旧文件时用；会重传全部日期，密码不变）。
W=~/claude-work/cf/node_modules/.bin/wrangler
mkdir -p $ST/functions; cd $ST
if [ ! -f .secret ]; then
  { echo "TOKEN=$(openssl rand -hex 8)"; echo "PASS=$(openssl rand -base64 18 | tr -dc 'A-Za-z0-9' | cut -c1-14)"; } > .secret; chmod 600 .secret
fi
if [ $ROTATE = 1 ]; then sed -i '' "s/^TOKEN=.*/TOKEN=$(openssl rand -hex 8)/" .secret; fi
. ./.secret
HASH=$(printf %s "$PASS" | shasum -a 256 | cut -d' ' -f1)
cat > functions/_middleware.js <<JS
// 预览站密码门：HTTP Basic（用户名随意）。仅用于 draft 预览部署，所有响应带 noindex。
const HASH = '$HASH';
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
export async function onRequest(ctx) {
  const auth = ctx.request.headers.get('Authorization') || '';
  let ok = false;
  if (auth.startsWith('Basic ')) {
    try {
      const pw = atob(auth.slice(6)).split(':').slice(1).join(':');
      ok = hex(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(pw))) === HASH;
    } catch (e) { ok = false; }
  }
  if (!ok) return new Response('Password required', { status: 401, headers: { 'WWW-Authenticate': 'Basic realm="Trending Scope draft", charset="UTF-8"', 'X-Robots-Tag': 'noindex, nofollow', 'Cache-Control': 'no-store' } });
  const res = await ctx.next();
  const out = new Response(res.body, res);
  out.headers.set('X-Robots-Tag', 'noindex, nofollow');
  out.headers.set('Cache-Control', 'no-store');
  return out;
}
JS
# 1) 视频 + 字幕 → R2 draft/<token>/
if [ $SKIP = 0 ]; then
  cd $M
  for f in $(find ${ONLY:-.} -type f \( -name '*.mp4' -o -name '*.vtt' -o -name '*.mp3' \) | sed 's#^\./##' | sort); do
    case $f in *.mp4) ct=video/mp4;; *.mp3) ct=audio/mpeg;; *.vtt) ct='text/vtt; charset=utf-8';; esac
    echo "put draft/$TOKEN/$f"; $W r2 object put "trending-videos/draft/$TOKEN/$f" --file "$f" --content-type "$ct" --cache-control "public, max-age=3600" --remote >/dev/null
  done
  cd $ST
fi
# 2) 构建（无统计代码，视频指向 draft 路径）
cd $S && python3 scripts/build_site.py --output $ST/dist --video-base "https://v.cosolution.cc/draft/$TOKEN" --preview
# 试点页（可选）：tools/pilot.html → /pilot/，媒体放 R2 的 draft/<token>/pilot/（用 --only=pilot 上传，源在 scope-media/v/pilot/）
if [ -f "$S/tools/pilot.html" ]; then mkdir -p $ST/dist/pilot && sed "s#__BASE__#https://v.cosolution.cc/draft/$TOKEN/pilot#g" "$S/tools/pilot.html" > $ST/dist/pilot/index.html; fi
# 3) 部署到 draft 分支
cd $ST && $W pages deploy dist --project-name=trending-scope --branch=draft --commit-dirty=true --commit-message="draft preview"
echo DRAFTDONE
