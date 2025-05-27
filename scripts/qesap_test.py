#!/usr/bin/env python3
"""
qesap_test.py – helper to launch the qe-sap test playbooks manually.

Quick positional usage:
python3 qesap_test.py <ACTION> <NODE_NAME> <SITE_NAME> <CSP> INSTANCE_ID> <INSTANCE_SID> <SAP_SIDADM>
Order is as depicted above for positional usage.

Named args > positional args > env_file args:
python3 qesap_test.py --playbook <playbook_name> --action <stop|crash|kill> --node-name <node_name> --site-name <site_name> \
    --cloud-user <cloud_user> --csp <csp> --instance-id <instance_id> --instance_sid <instance_sid> --sap-sidadm <sap_adm_name> \
    --inventory /path/to/inventory.yaml -vv

Defaults may also be provided in an *env_vars* file in the repo root:
Format is 'key: value' pair, one per each line. Comment lines with '#'.
cli args, if provided, override file args.

A combination of file and named/unnamed cli args can be used.

The script automatically sets ANSIBLE_ROLES_PATH and ANSIBLE_FILTER_PLUGINS to point
 at playbooks/roles and playbooks/filter_plugins unless you explicitly pass 
 --roles-path / --filter-path.
"""

import argparse
import os
import re
import shlex
import subprocess
import sys

REQUIRED = [
    'playbook', 'action', 'node_name', 'site_name', 'cloud_user',
    'csp', 'instance_id', 'instance_sid', 'sap_sidadm'
]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # …/qe-sap-testing
DEFAULT_ROLES  = os.path.join(REPO_ROOT, 'playbooks', 'roles')
DEFAULT_FILTER = os.path.join(REPO_ROOT, 'playbooks', 'filter_plugins')
DEFAULT_VARS   = os.path.join(REPO_ROOT, 'playbooks', 'vars', 'all.yml')
PLAYBOOK_DIR   = os.path.join(REPO_ROOT, 'playbooks')
ENV_FILE       = os.path.join(REPO_ROOT, 'env_vars')

def load_env_file(path):
    """read simple KEY: value file into dict (ignore blank / comment lines)"""
    vars_ = {}
    if not os.path.exists(path):
        return vars_
    with open(path) as f:
        for line in f:
            m = re.match(r'\s*([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$', line)
            if m:
                vars_[m.group(1).upper()] = m.group(2)
    return vars_

def merge_vars(positional, cli_named, env_file):
    """positional → dict via REQUIRED order, then overlay env_file, then cli"""
    merged = {}

    # map positional args
    for key, val in zip(REQUIRED, positional):
        merged[key] = val

    # add env file
    merged.update(env_file)

    # add cli named flags
    merged.update(cli_named)

    # create SAP_SIDADM if missing
    if not merged.get('sap_sidadm') and merged.get('instance_sid'):
        merged['sap_sidadm'] = merged['instance_sid'].lower() + 'adm'

    # required validation
    missing = [k for k in REQUIRED if not merged.get(k)]
    if missing:
        sys.exit(f"Missing required variables: {', '.join(missing)}")

    return merged

def format_vars(namespace):
    """Convert '-' to '_' in cli named vars"""
    return {
        k.replace('-', '_'): v
        for k, v in vars(namespace).items()
        if v is not None
    }


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)

    # named options (all optional, required checked later)
    parser.add_argument('--playbook', '-p')
    parser.add_argument('--action')
    parser.add_argument('--node-name')
    parser.add_argument('--site-name')
    parser.add_argument('--cloud-user')
    parser.add_argument('--csp')
    parser.add_argument('--instance-id')
    parser.add_argument('--instance-sid')
    parser.add_argument('--sap-sidadm')
    parser.add_argument('--inventory', required=True,
                        help='Ansible inventory YAML')
    parser.add_argument('--roles-path', default=DEFAULT_ROLES)
    parser.add_argument('--filter-path', default=DEFAULT_FILTER)
    parser.add_argument('--vars-file', default=DEFAULT_VARS)

    # catch extra ansible-playbook opts after “--”
    parser.add_argument('positional', nargs='*',
                        help='quick positional args in REQUIRED order')

    args, unknown = parser.parse_known_args()

    # format cli args
    cli_named = format_vars(args)

    # positional vars
    positional = args.positional
    if len(positional) > len(REQUIRED):
        sys.exit(f"Too many positional args (got {len(positional)}, "
                f"max {len(REQUIRED)})")

    # env file vars
    env_file_vars = load_env_file(ENV_FILE)

    # merge all vars respecting predecence
    combined = merge_vars(positional, cli_named, env_file_vars)

    # get chosen playbook
    pb_name = combined['playbook']
    chosen_playbook = os.path.join(PLAYBOOK_DIR, f"{pb_name}.yml")
    if not os.path.isfile(chosen_playbook):
        sys.exit(f"Playbook '{pb_name}.yml' not found in {PLAYBOOK_DIR}")

    env = os.environ.copy()
    env['ANSIBLE_ROLES_PATH']    = args.roles_path + ':' + env.get('ANSIBLE_ROLES_PATH', '')
    env['ANSIBLE_FILTER_PLUGINS'] = args.filter_path + ':' + env.get('ANSIBLE_FILTER_PLUGINS', '')
    env['ANSIBLE_HOST_KEY_CHECKING'] = 'False' 

    extra_vars = ' '.join(
        shlex.quote(f"{k}={v}") for k, v in combined.items())

    print(extra_vars)
    cmd = [
        'ansible-playbook',
        '-i', args.inventory,
        chosen_playbook,
        '-u', combined['cloud_user'],
        '-e', "@" + args.vars_file,
        '-e', extra_vars
    ]

    # forward any extra ansible flags
    if unknown:
        cmd.extend(unknown)

    print(cmd)
    print('Running:', ' '.join(shlex.quote(c) for c in cmd))
    proc = subprocess.run(cmd, env=env)

if __name__ == "__main__":
    main()
