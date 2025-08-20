import requests
import json
import logging
import time
from datetime import datetime
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

STAMP = round(datetime.now().timestamp())


def split_list_into_parts(lst, num_parts=10):
    k, m = divmod(len(lst), num_parts)
    return [
        lst[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(num_parts)
    ]


def clean_up_csv():
    df = pd.read_csv("Viper DB Tables For Syncing - Aug 2024 - Prod High_Priority.csv")
    df = df[
        df["Method"].isin(["Log-Based Incremental", "Cursor Incremental"])
    ]
    logging.info(f"Loaded {len(df)} tables for processing")
    return df


def request_with_retry(url, json_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=json_data)
            if response.status_code == 200:
                return response
            else:
                logging.warning(
                    f"Request failed with status {response.status_code}: {response.text}"
                )
        except requests.RequestException as e:
            logging.error(f"Network exception occurred: {e}")

        logging.info(f"Retrying {attempt + 1}/{max_retries}")
        time.sleep(5)

    logging.error("Max retries reached. Failing request.")
    return None


def spanwn_job(spanwed_name, schema, sync_reg, name, cursor_field=None):
    job_name = f"prod_hp_{STAMP}"

    podSpec = {
        "priorityClassName": "shakudo-job-default",
        "restartPolicy": "Never",
        "serviceAccountName": "gcr-pipelines",
        "nodeSelector": {"hyperplane.dev/nodeType": "hyperplane-meltano-small"},
        "tolerations": [
            {
                "key": "purpose",
                "operator": "Equal",
                "value": "meltano-small",
                "effect": "NoSchedule",
            }
        ],
        "volumes": [
            {
                "name": "custom-secret",
                "secret": {
                    "secretName": "custom-deploy-secrets-g994i1y2",
                    "defaultMode": 400,
                },
            },
            {
                "name": "gke-service-account-json",
                "secret": {"secretName": "service-account-key-pipelines-dccri9ba"},
            },
            {"name": "gitrepo", "emptyDir": {}},
            {
                "name": "github-key",
                "secret": {
                    "secretName": "client-repo-ritual-deploy-key",
                    "defaultMode": 400,
                },
            },
            {
                "name": "ipython-init",
                "configMap": {
                    "name": "hyperplane-settings",
                    "items": [{"key": "00_setup.py", "path": "00_setup.py"}],
                },
            },
            {
                "name": "snowflake-p8",
                "secret": {"secretName": "snowflake-p8", "defaultMode": 400},
            },
        ],
        "securityContext": {"fsGroup": 65533},
        "containers": [
            {
                "name": "d2v-pipeline",
                "workingDir": "/tmp/git/monorepo/",
                "ports": [
                    {"name": "http", "containerPort": 8787, "protocol": "TCP"},
                    {"name": "ssh", "containerPort": 22, "protocol": "TCP"},
                ],
                "envFrom": [{"configMapRef": {"name": "hyperplane-settings"}}],
                "env": [
                    {
                        "name": "MY_IMAGE",
                        "value": "gcr.io/hyperplane-test/custom/ritual/meltano-runner@sha256:db4cafb4e7f46b233fc9664df29f358603119dfa5977910589b51b8d33cecf87",
                    },
                    {
                        "name": "MY_POD_NAME",
                        "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}},
                    },
                    {
                        "name": "MY_POD_NAMESPACE",
                        "valueFrom": {"fieldRef": {"fieldPath": "metadata.namespace"}},
                    },
                    {
                        "name": "ISTIO_GATEWAY",
                        "value": "hyperplane-istio/ingress-gateway-c7rnu4qu",
                    },
                    {"name": "PYARROW_IGNORE_TIMEZONE", "value": "1"},
                    {"name": "HYPERPLANE_GPU_SESSION", "value": "false"},
                    {
                        "name": "MY_NODE_IP",
                        "valueFrom": {"fieldRef": {"fieldPath": "status.podIP"}},
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_RSA_KEY",
                        "valueFrom": {
                            "secretKeyRef": {"name": "snowflake-p8", "key": "rsa-key"}
                        },
                    },
                    {"name": "HYPERPLANE_JOB_CHECKED_COMMIT_ID", "value": ""},
                    {
                        "name": "HYPERPLANE_JOB_CHECKED_BRANCH_NAME",
                        "value": "nat_test",
                    },
                    {"name": "HYPERPLANE_JOB_DEBUGGABLE", "value": "false"},
                    {"name": "PIPELINES_USER", "value": "stella"},
                    {
                        "name": "HYPERPLANE_JOB_PIPELINE_YAML_PATH",
                        "value": "meltano-mysql-snowflake-job/run_prod_hp.yaml",
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_ACCOUNT",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "target-snowflake-secret",
                                "key": "TARGET_SNOWFLAKE_ACCOUNT",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_DB",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "target-snowflake-secret",
                                "key": "TARGET_SNOWFLAKE_DB",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_ROLE",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "target-snowflake-secret",
                                "key": "TARGET_SNOWFLAKE_ROLE",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_SCHEMA",
                        "value": "MELTANO_VIPER_PROD_HIGH_PRIORITY"
                        # "valueFrom": {
                        #     "secretKeyRef": {
                        #         "name": "target-snowflake-secret",
                        #         "key": "TARGET_SNOWFLAKE_SCHEMA",
                        #     }
                        # },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_SECRET_PATH",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "target-snowflake-secret",
                                "key": "TARGET_SNOWFLAKE_SECRET_PATH",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_USER",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "target-snowflake-secret",
                                "key": "TARGET_SNOWFLAKE_USER",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_WH",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "target-snowflake-secret",
                                "key": "TARGET_SNOWFLAKE_WH",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_TABLE_PREFIX",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "target-snowflake-secret",
                                "key": "TARGET_TABLE_PREFIX",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_DB",
                        # "value": f"{schema}",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "source-mysql-secret-prod",
                                "key": "SOURCE_MYSQL_DB",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_HOST",
                        # "value": "10.64.7.210"
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "source-mysql-secret-prod",
                                "key": "SOURCE_MYSQL_HOST",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_PORT",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "source-mysql-secret-prod",
                                "key": "SOURCE_MYSQL_PORT",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_PW",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "source-mysql-secret-prod",
                                "key": "SOURCE_MYSQL_PW",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_USER",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "source-mysql-secret-prod",
                                "key": "SOURCE_MYSQL_USER",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_RSA_KEY",
                        "valueFrom": {
                            "secretKeyRef": {"name": "snowflake-p8", "key": "rsa-key"}
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_AWS_ACCESS_KEY_ID",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "meltano-minio-secret",
                                "key": "AWS_ACCESS_KEY_ID",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_AWS_ENDPOINT_URL",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "meltano-minio-secret",
                                "key": "AWS_ENDPOINT_URL",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_AWS_SECRET_ACCESS_KEY",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "meltano-minio-secret",
                                "key": "AWS_SECRET_ACCESS_KEY",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_CUSTOM_SECRET_KEY_MELTANO_STATE_BACKEND_URI",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "meltano-minio-secret",
                                "key": "MELTANO_STATE_BACKEND_URI",
                            }
                        },
                    },
                    {
                        "name": "HYPERPLANE_JOB_PARAMETER_REGEX_TO_SYNC",
                        "value": f"{sync_reg}",
                    },
                    {
                        "name": "HYPERPLANE_JOB_PARAMETER_INCREMENTAL_KEY",
                        "value": cursor_field or "",
                    },
                ],
                "image": "gcr.io/hyperplane-test/custom/ritual/meltano-runner@sha256:db4cafb4e7f46b233fc9664df29f358603119dfa5977910589b51b8d33cecf87",
                # "image": "gcr.io/hyperplane-test/custom/ritual/meltano-runner@sha256:db4cafb4e7f46b233fc9664df29f358603119dfa5977910589b51b8d33cecf87",
                "command": ["/bin/bash"],
                "args": [
                    "-c",
                    "env > /etc/environment && echo $SERVICE_ACCOUNT_KEY_CONTENT >  /etc/service_account_key_content && chmod +x /tmp/git/monorepo/meltano-mysql-snowflake-job/run_prod_hp.sh && /tmp/git/monorepo/meltano-mysql-snowflake-job/run_prod_hp.sh",
                ],
                "volumeMounts": [
                    {
                        "name": "custom-secret",
                        "mountPath": "/etc/hyperplane/secrets",
                        "readOnly": True,
                    },
                    {"name": "gitrepo", "mountPath": "/tmp/git"},
                    {
                        "name": "gke-service-account-json",
                        "mountPath": "/etc/gke-service-account-json",
                        "readOnly": True,
                    },
                    {"name": "ipython-init", "mountPath": "/etc/ipython_startup"},
                    {
                        "name": "snowflake-p8",
                        "mountPath": "/etc/hyperplane/secrets/snowflake_p8",
                        "readOnly": True,
                    },
                ],
                "resources": {
                    "limits": {"cpu": "2200m", "memory": "120Gi"},
                    "requests": {"cpu": "300m", "memory": "2Gi"},
                },
            },
            {
                "name": "sidecar-terminator",
                "image": "gcr.io/devsentient-infra/dev/sidecar-terminator:0f74575067e596d757590ee7e5a7536eb5ab53e7",
                "ports": [{"name": "http", "containerPort": 9092, "protocol": "TCP"}],
                "env": [
                    {
                        "name": "MY_POD_NAME",
                        "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}},
                    },
                    {
                        "name": "MY_POD_NAMESPACE",
                        "valueFrom": {"fieldRef": {"fieldPath": "metadata.namespace"}},
                    },
                ],
            },
        ],
        "initContainers": [
            {
                "name": "git-sync-init",
                "image": "gcr.io/hyperplane-test/custom/ritual/meltano-runner@sha256:db4cafb4e7f46b233fc9664df29f358603119dfa5977910589b51b8d33cecf87",
                "command": ["/bin/sh"],
                "args": [
                    "-c",
                    'mkdir /root/.ssh && cp /etc/git-secret/* /root/.ssh/ && chmod 400 /root/.ssh/id_rsa && ((GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no" git clone --depth 1 --branch nat_test git@github.com:devsentient/client-repo-ritual.git /tmp/git/monorepo))',
                ],
                "volumeMounts": [
                    {"name": "gitrepo", "mountPath": "/tmp/git"},
                    {
                        "name": "github-key",
                        "mountPath": "/etc/git-secret",
                        "readOnly": True,
                    },
                ],
                "resources": {"limits": {"cpu": "200m", "memory": "512Mi"}},
            },
        ],
    }

    json_data = {
        "operationName": "createPipelineJobWithAlerting",
        "variables": {
            "jobName": f"{job_name}",
            "type": "basic",
            "imageHash": "",
            "noHyperplaneCommands": False,
            "debuggable": False,
            "notificationsEnabled": False,
            "timeout": 14400,
            "activeTimeout": 14400,
            "maxRetries": 0,
            "customMessage": f"[prod_hp], {schema}, {name}",
            "yamlPath": "meltano-mysql-snowflake-job/run_prod_hp.yaml",
            "noGitInit": False,
            "hyperplaneSecrets": [
                # {
                #     "id": "684c580b-d1d7-46a2-b985-9024d50a302d"
                # },
                # {
                #     "id": "ae3dfeb1-a50f-44aa-a2e3-6a08f566ba0f"
                # },
                # {
                #     "id": "6c1a30f3-859f-437f-8c4a-5ac8ba1a8791"
                # },
                # {
                #     "id": "47ac4da7-53d4-4ac7-b354-61a25b66dc89"
                # }
            ],
            "hyperplaneVCServerId": {"id": "7bc78e07-709e-4c0d-8490-167c23947208"},
            "branchName": "nat_test",
            "commitId": "",
            "parameters": {"create": []},
            "hyperplaneUserId": "048bdfdf-efb6-44e9-8271-14bc6a2113f0",
            "hyperplaneUserEmail": "shakudo-admin@shakudo.io",
            "group": "",
            "podSpec": json.dumps(podSpec),
            "cloudSqlProxyEnabled": False,
            "pipelineType": "YAML",
        },
        "query": "mutation createPipelineJobWithAlerting($customMessage: String!, $jobName: String!, $type: String!, $imageHash: String, $noHyperplaneCommands: Boolean, $debuggable: Boolean!, $notificationsEnabled: Boolean, $notificationTargetIds: [String!], $timeout: Int!, $activeTimeout: Int, $maxRetries: Int!, $schedule: String, $timezone: String, $yamlPath: String!, $noGitInit: Boolean, $hyperplaneVCServerId: HyperplaneVCServerWhereUniqueInput, $billingProjectId: BillingProjectWhereUniqueInput, $hyperplaneSecrets: [HyperplaneSecretWhereUniqueInput!], $branchName: String, $commitId: String, $parameters: ParameterCreateNestedManyWithoutPipelineJobInput, $hyperplaneUserId: String!, $hyperplaneUserEmail: String!, $group: String, $podSpec: String, $hyperplaneServiceAccountId: HyperplaneServiceAccountWhereUniqueInput, $cloudSqlProxyEnabled: Boolean, $hyperplaneCloudSqlProxyId: String, $pipelineType: String) {\n  createPipelineJobWithAlerting(\n    input: {jobName: $jobName, jobType: $type, imageHash: $imageHash, noHyperplaneCommands: $noHyperplaneCommands, debuggable: $debuggable, notificationsEnabled: $notificationsEnabled, notificationTargetIds: $notificationTargetIds, timeout: $timeout, activeTimeout: $activeTimeout, maxRetries: $maxRetries, schedule: $schedule, pipelineYamlPath: $yamlPath, noGitInit: $noGitInit, hyperplaneVCServer: {connect: $hyperplaneVCServerId}, billingProject: {connect: $billingProjectId}, hyperplaneSecrets: {connect: $hyperplaneSecrets}, branchName: $branchName, commitId: $commitId, customMessage: $customMessage, parameters: $parameters, timezone: $timezone, hyperplaneUser: {connect: {id: $hyperplaneUserId}}, hyperplaneUserEmail: $hyperplaneUserEmail, group: $group, podSpec: $podSpec, hyperplaneServiceAccount: {connect: $hyperplaneServiceAccountId}, cloudSqlProxyEnabled: $cloudSqlProxyEnabled, hyperplaneCloudSqlProxyId: $hyperplaneCloudSqlProxyId, pipelineType: $pipelineType}\n  ) {\n    id\n    pinned\n    pipelineYamlPath\n    jobName\n    schedule\n    status\n    statusReason\n    output\n    startTime\n    completionTime\n    daskDashboardUrl\n    dashboardPrefix\n    timeout\n    timezone\n    outputNotebooksPath\n    activeTimeout\n    maxRetries\n    exposedPort\n    jobType\n    noVSRewrite\n    minReplicas\n    maxHpaRange\n    debuggable\n    notificationsEnabled\n    notificationTargets {\n      notificationTarget {\n        email\n      }\n    }\n    sshCommand\n    imageHash\n    noGitInit\n    branchName\n    commitId\n    branchNameOrCommit\n    hyperplaneUserEmail\n    displayedOwner\n    noHyperplaneCommands\n    group\n    hyperplaneServiceAccountId\n    grafanaLink\n    parameters {\n      key\n      value\n    }\n    userServiceSubdomain\n    pipelineType\n  }\n}\n",
    }

    url = "http://api-server.hyperplane-core.svc.cluster.local:80/graphql"
    response = request_with_retry(url, json_data)

    if response and response.status_code == 200:
        data = response.json()
        pipeline_data = data.get("data", {})
        job_info = pipeline_data.get("createPipelineJobWithAlerting", {})
        job_id = job_info.get("id")
        if job_id:
            logging.info(f"Spawn job query successful for regex: {sync_reg}")
            return job_id
        else:
            logging.error(
                f"Failed to spawn job with regex with status code 200: {sync_reg}"
            )
            logging.error(f"Response: {json.dumps(response.json(), indent=4)}")
            return None
    else:
        logging.error(f"Failed to spawn job with regex: {sync_reg}")
        return None


def main():
    df = clean_up_csv()
    list_of_dicts = df.to_dict(orient="records")
    status_dict = {
        f'{tbl["Schema"]}-{tbl["Table Names"]}': "pending" for tbl in list_of_dicts
    }
    job_2_id = {f'{tbl["Schema"]}-{tbl["Table Names"]}': None for tbl in list_of_dicts}
    all_done = False
    num_concurrent = 0
    while not all_done:
        not_done_count = sum(1 for status in status_dict.values() if status != "done")
        logging.info(f"The number of jobs not yet done: {not_done_count}")
        for k, v in status_dict.items():
            if v == "pending":
                if num_concurrent >= 40:
                    continue
                schema, name = k.split("-")
                row = df[(df["Schema"] == schema) & (df["Table Names"] == name)].iloc[
                    0
                ]  
                sync_reg = (
                    f"!{schema}-actual_count:!{schema}-ac:!{schema}-v_*:{schema}-{name}"
                )
                cursor_field = (
                    row["Cursor field"]
                    if row["Method"] == "Cursor Incremental"
                    else None
                )  
                id_ = spanwn_job(
                    f"{schema}-{name}", schema, sync_reg, name, cursor_field
                )  
                if id_:
                    status_dict[k] = "running"
                    job_2_id[k] = id_
                    num_concurrent += 1
                    time.sleep(2)
                else:
                    logging.warning(f"Job {k} not created, retrying after delay")
            elif v == "running":
                id_ = job_2_id[k]
                url = "http://api-server.hyperplane-core.svc.cluster.local:80/graphql"
                payload = {
                    "query": f"""
                        query {{
                            pipelineJob(where: {{id: "{id_}"}}) {{
                                status
                            }}
                        }}
                    """
                }
                response = request_with_retry(url, payload)
                if response:
                    status = (
                        response.json()
                        .get("data", {})
                        .get("pipelineJob", {})
                        .get("status")
                    )
                    if status:
                        logging.info(f"Job {k} current status: {status}")
                        if status == "failed":
                            logging.error(
                                f"Ritual Sync job [PROD HIGH PRIORITY] [{id_}] failed, please check logs"
                            )
                        if status in ["done", "failed"]:
                            logging.info(f"Job {k} completed with status {status}")
                            del job_2_id[k]
                            num_concurrent -= 1
                            status_dict[k] = "done"
                        if status == "pending":
                            logging.info(
                                f"Job {k} still in pending state, will create other jobs after delay"
                            )
                            time.sleep(30)
                            logging.info(f"Trying to create new jobs now")

        if not any(value in ["pending", "running"] for value in status_dict.values()):
            all_done = True
            logging.info("All jobs completed. Exiting loop.")
            break
        logging.info(f"Sleeping for 30 seconds before next check")
        time.sleep(30)
        logging.info(f"Starts next checks")


if __name__ == "__main__":
    main()