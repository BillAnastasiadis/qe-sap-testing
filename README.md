# QE-SAP-TESTING (WIP)

qe-sap-testing is a sister repository to https://github.com/SUSE/qe-sap-deployment. It uses ansible to run tests on the deployments created by `qe-sap-deployment`. 

## Installation

Clone the repository in a system which has `qe-sap-deployment` cloned.

## Usage

Create a deployment with qe-sap-deployment. Then navigate to `/testing_repo_path/qe-sap-testing/`. 

**BELOW SECTION IS WIP, ONLY APPLIES TO RUN OF hana_sr_takeover FOR NOW:**

You need to set some variables in order to run the tests of this repo manually:

```bash
export SAP_SIDADM=...
export INSTANCE_ID=...
export INSTANCE_SID=...

# export the paths of the new variables file and plugin directory
export ANSIBLE_FILTER_PLUGINS=\$PWD/playbooks/filter_plugins:${ANSIBLE_FILTER_PLUGINS:-} 
export ANSIBLE_ROLES_PATH=\$PWD/playbooks/roles:${ANSIBLE_ROLES_PATH:-}
ACTION=crash|stop|kill
SITE=<site_name>
NODE=<node_name>
```

After you set the appropriate variables, run the hana_sr_takeover playbook:

```bash
ansible-playbook -i /<deployment_repo_path>/qe-sap-deployment/terraform/<your_csp>/inventory.yaml playbooks/hana_sr_takeover.yml -u <cloud_admin_user> -e "@/<testing_repo_path>/qe-sap-testing/playbooks/vars/all.yml" -e "action=$ACTION node_name=$NODE site_name=$SITE sap_sidadm=$SAP_SIDADM instance_id=$INSTANCE_ID" -vv
```

To run the easy way with the script, look at the script description (TBD)

## Contributing

Pull requests welcome.