
import os
import subprocess
import sys

from tools.path_utils import resolve_from_project_root

script_path = resolve_from_project_root("__006__streamlit/__001__streamlit_chat_page.py")
print(script_path)

python_dir = os.path.dirname(sys.executable)
streamlit_exe = os.path.join(python_dir, "streamlit.exe")
if not os.path.exists(streamlit_exe):
    streamlit_exe = "streamlit"

certifi_path = os.path.join(python_dir, "Lib", "site-packages", "certifi", "cacert.pem")
if os.path.exists(certifi_path):
    os.environ["SSL_CERT_FILE"] = certifi_path

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ["PYTHONPATH"] = resolve_from_project_root("")

subprocess.run([streamlit_exe, "run", script_path])
