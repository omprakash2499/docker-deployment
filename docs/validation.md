# Validation record

## Observed results

| Check | Evidence/result |
| --- | --- |
| Application unit tests | Nine tests passed in Jenkins build #4 on Python 3.13.5 |
| SQLite connection closure | Regression test passed for successful and failed requests |
| Docker image build and container smoke test | Passed in Jenkins build #4 |
| Local Compose health and smoke checks | Container healthy; /health and /incidents PASS |
| Local persistence | Incident survived Compose down/up using its named volume |
| Local stop/start recovery | Smoke failed while stopped, passed after restart; incident retained |
| ECR publication | Image pushed and identified by digest |
| AWS deployment | SSM release reported Release healthy; Jenkins Finished: SUCCESS |
| EC2 API verification | Healthy container, /health OK, incident created and listed |
| Terraform cleanup | 12 resources destroyed successfully |

Application commit: `192fadf35de4a8d9ae11f897a3999845b6100acc`.
Pipeline commit: `218b4ceef47d544c74fa010e55a1cb78c8cc9759`.
Deployed image digest: `sha256:ef010867d4157c0b8712b61ae45aa3901a9350bc99a83ed607d9fb2697c8b078`.

[Build and runtime screenshots](https://github.com/omprakash2499/jenkins-cicd-deployment/tree/main/docs/screenshots) show the recorded deployment. The AWS demo is no longer running after cleanup.

## Limits

Windows execution of the corrected unit suite was not separately confirmed in the supplied output. The nine-test Linux Jenkins run is confirmed. AWS persistence across container replacement, automated rollback, load testing, high availability and vulnerability scan results have not been verified. Local persistence evidence must not be described as AWS recovery evidence.

Earlier authoring checks covered HTTP behavior, input validation, database health and SQLite persistence; the later container and Jenkins runs above supersede the original pending-runtime status.
