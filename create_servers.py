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

from pymongo import MongoClient
#MONGO_CONNECTION = os.getenv('MONGO')
#con = MongoClient('mongodb://mongodb:27021')
con = MongoClient('mongodb://localhost:27021')
db = con['cluster']
col_servers = db['servers']

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
    col_servers.insert_one({
        "ip": IP.group(),
	"status": "free",
	"name": name 
})
    return IP.group()

def get_free_server(cluster, role):
  server_info = col_servers.find_one({"status": "free"})
  col_servers.update_one({'_id': server_info['_id']}, {'$set': {'cluster': cluster, 'role': role, "status": "used"}})
  return server_info

def create_cluster():
  ha_server = get_free_server(CLUSTER_NAME, 'HA')
  ha_ip = ha_server['ip']
  f = open('hacfg.tmpl')
  tmpl = f.read()
  f.close()
  #TODO Need to edit for multiple masters
  #master_servers = [get_free_server(CLUSTER_NAME, "Master")]
  master_servers = []
  for i in range(MASTER_COUNT):
    master_servers.append(get_free_server(CLUSTER_NAME, "Master"))
  #master_server_ip = [master_server['ip']]
  backend = ""
  hosts = ""
  for item in master_servers:
      backend += "  server %s %s:6443 check fall 3 rise 2\n" % (item['name'],item['ip'])
      hosts += "%s %s\n" % (item['ip'], item['name'])
  tmpl = tmpl % (ha_ip, backend)
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

def get_masters(cluster):
    result = col_servers.find({'role': "Master", 'cluster': cluster})
    return list(result)

def get_ha(cluster):
    result = col_servers.find_one({'role': "HA", 'cluster': cluster})
    return result
    
def activate_masters():
    ips = ""
    for master in get_masters(CLUSTER_NAME):
      os.system('ssh-keygen -f "/home/ubuntu/.ssh/known_hosts" -R "%s"' % master['ip'])
      ips += master['ip'] + ","
    command = "ansible-playbook activate-masters.yml -e 'ha_ip=%s' -i %s" % (get_ha(CLUSTER_NAME)['ip'], ips)
    if print_mode:
      print(command)
    else:
      output = subprocess.check_output(command, shell=True).decode()
    #print(output)

def join_worker():
    command = "ansible-playbook token.yml -i %s," % get_masters(CLUSTER_NAME)[0]['ip']
    print(command)
    if print_mode:
      print(command)
    else:
      output = subprocess.check_output(command, shell=True).decode()
    
    worker = get_free_server(CLUSTER_NAME, 'Worker')

    command = "ansible-playbook join-worker.yml -i %s," % worker['ip']
    print(command)
    if print_mode:
      print(command)
    else:
      output = subprocess.check_output(command, shell=True).decode()


#create_cluster()
#activate_masters()
join_worker()
#for i in range(20):
#  create_server('node' + str(i))


