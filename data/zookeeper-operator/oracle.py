import json
from typing import List
from client.oracle_handle import OracleHandle
from common import ErrorResult, Oracle, PassResult, RunResult


def zookeeper_checker(handle: OracleHandle) -> RunResult:
    '''Checks the health of the Zookeeper cluster'''

    sts_list = handle.get_stateful_sets()

    if len(sts_list) != 1:
        return ErrorResult(oracle=Oracle.CUSTOM,
                           msg='Zookeeper cluster has more than one stateful set')

    pod_list = handle.get_pods_in_stateful_set(sts_list[0])

    leaders = 0

    for pod in pod_list:
    	if pod.status.pod_ip == None:
	    return ErrorResult(oracle=Oracle.CUSTOM, msg='Zookeeper pod does not have an IP assigned')
        p = handle.kubectl_client.exec(
            pod.metadata.name, pod.metadata.namespace,
            ['curl', 'http://' + pod.status.pod_ip + ':8080/commands/ruok'], capture_output=True, text=True)
        result = json.loads(p.stdout)
        if result['error'] != None:
            return ErrorResult(oracle=Oracle.CUSTOM, msg='Zookeeper cluster curl has error')

        p = handle.kubectl_client.exec(
            pod.metadata.name, pod.metadata.namespace,
            ['curl', 'http://' + pod.status.pod_ip + ':8080/commands/stat'], capture_output=True, text=True)
        result = json.loads(p.stdout)
        if result['error'] != None:
            return ErrorResult(oracle=Oracle.CUSTOM, msg='Zookeeper cluster curl has error')
        elif result['server_stats']['server_state'] == 'leader':
            leaders += 1

    if leaders > 1:
        return ErrorResult(oracle=Oracle.CUSTOM, msg='Zookeeper cluster has more than one leader')

    return PassResult()


CUSTOM_CHECKER: List[callable] = [zookeeper_checker]
