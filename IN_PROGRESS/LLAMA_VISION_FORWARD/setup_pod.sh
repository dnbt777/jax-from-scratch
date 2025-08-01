# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# install neovim
curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux-x86_64.tar.gz
rm -rf /opt/nvim
tar -C /opt -xzf nvim-linux-x86_64.tar.gz
rm nvim-linux-x86_64.tar.gz
echo 'export PATH="$PATH:/opt/nvim-linux-x86_64/bin"' >> ~/.bashrc

apt update
apt install -y tmux



# sync uv
/root/.local/bin/uv sync

# install vllm
/root/.local/bin/uv pip install -U vllm --extra-index-url https://wheels.vllm.ai/nightly

# overwrite vllm mllama
cp ./custom_vllm/mllama.py ./.venv/lib/python3.12/site-packages/vllm/model_executor/models/mllama.py

exec bash
