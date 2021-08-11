import os
os.environ["OS_DOMAIN_ID"] = "default"
os.environ["OS_DOMAIN_NAME"] = "default"
import subprocess
import re
MASTER_COUNT = 2
WORKER_COUNT = 3
CLUSTER_NAME = 'Auto'

if not os.path.exists('temp'):
  os.makedirs('temp')

def create_server(name):
  output = subprocess.check_output("ansible-playbook /home/ubuntu/private-playoobks/tabriz_node.yml -e 'name=%s'" % name, shell=True).decode()
  pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
  IP = pat.search(output)
  return IP.group()

def create_masters():
  f = open('temp/%s_masters.txt' % CLUSTER_NAME, 'w')
  for i in range(MASTER_COUNT):
    IP = create_server(CLUSTER_NAME+ '_master' + str(i))
    f.write(IP+'\n')
  f.close()

def create_HA():
  IP = create_server(CLUSTER_NAME+ '_HA')
  f = open('temp/%s_HA.txt' % CLUSTER_NAME, 'w')
  f.write(IP+'\n')
  f.close()

def HA_config():
  f = open('hacfg.tmpl')
  tmpl = f.read()
  f.close()
  f = open('temp/' + CLUSTER_NAME + '_HA.txt')
  ha_ip = f.read().strip()
  f.close()
  f = open('temp/' + CLUSTER_NAME + '_masters.txt')
  masters = f.readlines()
  backend = ""
  for i, item in enumerate(masters):
      backend += "  server kmaster%s %s:6443 check fall 3 rise 2\n" % (i, item.strip())
  tmpl = tmpl % (ha_ip, backend)
  print(tmpl)
  f = open('temp/haproxy.cfg', 'w')
  f.write(tmpl)
  f.close()
create_HA()
create_masters()
HA_config()

