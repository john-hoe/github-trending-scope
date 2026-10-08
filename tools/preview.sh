# 在 Mac 上：重新构建 → 链接视频素材 → 确保 8082 预览服务在跑
export PATH=/opt/homebrew/bin:$PATH
cd ~/claude-work/scope-site && python3 scripts/build_site.py --output ~/claude-work/scope-dist --video-base /v --preview || exit 1
ln -sfn ~/claude-work/scope-media/v ~/claude-work/scope-dist/v
tmux has-session -t scopepreview 2>/dev/null || tmux new-session -d -s scopepreview "python3 ~/claude-work/scope-site/tools/serve-site.py 8082 ~/claude-work/scope-dist"
echo preview http://100.103.240.12:8082/
