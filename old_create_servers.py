import os
os.environ["OS_DOMAIN_ID"] = "default"
os.environ["OS_DOMAIN_NAME"] = "default"
import subprocess
import re
import sys
from random import randint
MASTER_COUNT = 2
WORKER_COUNT = 3
CLUSTER_NAME = 'D'

if not os.path.exists('temp'):
  os.makedirs('temp')


print_mode= False
if len(sys.argv) > 1:
    print_mode = sys.argv[1] == 'print'
#print(print_mode)

def create_server(name):
  command = "ansible-playbook /home/ubuntu/private-playoobks/tabriz_node.yml -e 'name=%s'" % name
  if print_mode:
      print(command)
      return 'SERVER_IP' + str(randint(1, 100))
  else:
    output = subprocess.check_output(command, shell=True).decode()
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

def get_ha_ip():
  f = open('temp/' + CLUSTER_NAME + '_HA.txt')
  ha_ip = f.read().strip()
  f.close()
  return ha_ip

def get_masters_ip():
  f = open('temp/' + CLUSTER_NAME + '_masters.txt')
  masters = f.readlines()
  f.close()
  ips = [ip.strip() for ip in masters]
  return ips

def HA_config():
  ha_ip = get_ha_ip()
  f = open('hacfg.tmpl')
  tmpl = f.read()
  f.close()
  masters = get_masters_ip()
  backend = ""
  hosts = ""
  for i, item in enumerate(masters):
      backend += "  server kmaster%s %s:6443 check fall 3 rise 2\n" % (i, item)
      hosts += "%s kmaster%s\n" % (item.strip(), i)
  tmpl = tmpl % (ha_ip, backend)
  #print(tmpl)
  f = open('temp/haproxy.cfg', 'w')
  f.write(tmpl)
  f.close()

  # Creating /etc/hosts
  f = open('temp/hosts', 'w')
  hosts = "127.0.0.1 localhost\n" + hosts
  f.write(hosts)
  f.close()
  command = "ansible-playbook config-ha.yml -i %s," % ha_ip
  if print_mode:
      print(command)
  else:
    output = subprocess.check_output(command, shell=True).decode()

def activate_masters():
    ips = ""
    for ip in get_masters_ip():
      #os.system('ssh-keygen -f "/home/ubuntu/.ssh/known_hosts" -R "%s"' % ip)
      ips += ip + ","
    command = "ansible-playbook activate-masters.yml -e 'ha_ip=%s' -i %s" % (get_ha_ip(), ips)
    if print_mode:
      print(command)
    else:
      output = subprocess.check_output(command, shell=True).decode()
    #print(output)
   

create_HA()
create_masters()
HA_config()
activate_masters()

