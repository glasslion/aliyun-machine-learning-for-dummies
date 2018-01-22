# Set options for certfile, ip, password, and toggle off browser auto-opening
c.NotebookApp.certfile = u'/home/ml/.jupyter/mycert.pem'
c.NotebookApp.keyfile = u'/home/ml/.jupyter/mykey.key'
# Set ip to '*' to bind on all interfaces (ips) for the public server
c.NotebookApp.ip = '*'
c.NotebookApp.open_browser = False
c.NotebookApp.notebook_dir = '/mnt/ml/working'

# It is a good idea to set a known, fixed port for server access
c.NotebookApp.port = 8888