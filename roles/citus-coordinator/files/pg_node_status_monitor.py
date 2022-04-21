import argparse
import csv
import subprocess
import sys
import io

parser = argparse.ArgumentParser()
parser.add_argument('-H','--pgpool-host', default='127.0.0.1')
parser.add_argument('-p','--pgpool-port', default=9999)
parser.add_argument('-P','--pgpool-pcp-port', default=9898)
args = parser.parse_args()

pool_stats_cmd = ['/usr/bin/psql', '-h', args.pgpool_host,
                  '-p', str(args.pgpool_port),
                  '-c', 'show pool_nodes', '--csv']

proc = subprocess.Popen(pool_stats_cmd, stdout=subprocess.PIPE, stderr=sys.stderr)
ecode = proc.wait()
if ecode:
    sys.exit(1)

reader = csv.DictReader(io.StringIO(proc.stdout.read().decode('utf8')))

fail = False
for node in reader:
    if node['status'] != 'down':
       continue 
    if node['pg_status'] != 'up':
       continue
    
    attach_node_cmd = ['/usr/bin/pcp_attach_node', '-h', args.pgpool_host,
                       '-p', str(args.pgpool_pcp_port), '-n', node['node_id'], '-w']
    print("Attaching node %s (%s)" % (node['node_id'], node['hostname']))
    ecode = subprocess.Popen(attach_node_cmd, stdout=sys.stdout, stderr=sys.stderr).wait()
    if ecode:
        fail = True

if fail:
    sys.exit(3)

