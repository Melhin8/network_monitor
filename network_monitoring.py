import os
import logging
import subprocess
from time import sleep


def bash_call(param: str) -> int:
    """run nmcli in bash

    Args:
        param (str): parameters for nmcli

    Returns:
        subprocess.call (int): subprocess code
    """
    return subprocess.call(f'nmcli {param}', shell=True)


def bash_output(param: str) -> str:
    """run command in bash and return its output

    Args:
        param (str): command with parametrs

    Returns:
        str: commands output
    """
    return subprocess.check_output(param, shell=True).decode('utf-8')


def reboot_networking():
    bash_call('networking off')
    logging.info('networking off')
    sleep(2)
    bash_call('networking on')
    logging.info('networking on')
    sleep(2)


def reboot_wifi(hotspot: str) -> None:
    bash_call(f'c up {hotspot}')
    logging.info(f'Local network is done, up {hotspot}')


def select_device() -> str:
    """scan and select network adapter

    Returns:
        str: selected adapter
    """
    dirty_arp = bash_output('nmcli d | grep wifi')
    list_dirty_arp = [i.split() for i in dirty_arp.split('\n')]
    device = [i[0] for i in list_dirty_arp if 'wifi' in i]
    return device[0]


def select_hotspot(device=select_device()) -> str:
    """run `nmcli c` and filtred by wifi and selected network adapter

    Args:
        device (str, optional): selected network adapter. Defaults to select_device().

    Returns:
        str: name wifi conection
    """
    return bash_output(f'nmcli c | awk "/wifi/ && /{device}/"').split()[0]


def ping(host: str, params: str, grep: str) -> str:
    """run ping with some parameters and grep

    Args:
        host (str): host who ping
        params (str): params to ping
        grep (str): what exactly grep with word `grep`

    Returns:
        str: ping output
    """
    try:
        pong = bash_output(f'ping {host} {params} | {grep}')
    except Exception:
        logging.error(f'faled ping {host} {params} | {grep}')
        pong = None
    return pong


def select_ip(device=select_device()) -> str:
    """scan local network and select ip with min avg ping.
    If wifi adapter is down - up it

    Args:
        device (str, optional): selected network adapter. Defaults to select_device().

    Returns:
        str: selected ip
    """
    try:
        arp = bash_output(f'arp -ni {device} | grep ether')
    except Exception:
        logging.error('WI-FI off')
        bash_call('radio wifi on')
        sleep(5)
        logging.info('WI-FI on')
        return select_ip()
    ip_list = [i.split()[0] for i in arp.strip().split('\n')]
    ping_dict = {}
    for ip in ip_list:
        try:
            value = ping(ip, '-c 3', 'grep /').split('=')[1].split('/')[1]
            ping_dict[ip] = float(value)
        except Exception:
            continue
    if ping_dict:
        selected_ip = min(ping_dict, key=ping_dict.get)
        logging.info(f'Ip selected: {selected_ip}')
    else:
        logging.warning('No local ip')
        selected_ip = select_ip()  # TODO: fix potential infinite cycle
    return selected_ip


def local_ping(selected_ip: str) -> tuple(str, str):
    """ping ip and change it if ping is None

    Args:
        selected_ip (str): ip with min avg ping

    Returns:
        tuple (str, str): (output ping, ip what ping)
    """
    dirty_avg = ping(selected_ip, '-c 5', 'grep /')
    if dirty_avg is None:
        logging.error('Local ping is None')
        sleep(5)
        dirty_avg, selected_ip = local_ping(select_ip())
        logging.warning(f'New local ip selected: {selected_ip}')
    return dirty_avg, selected_ip


def local_avg(selected_ip: str) -> tuple(float, str):
    """checks `local_ping` and filters the avg ping

    Args:
        selected_ip (str): ip with min avg ping

    Returns:
        tuple(float, str): (avg ping, ip what ping)
    """
    dirty_avg, selected_ip = local_ping(selected_ip)
    avg_local = float(dirty_avg.split('=')[1].split('/')[1])
    return avg_local, selected_ip


def host_ping(host: str) -> str:
    """ping host

    Args:
        host (str): 8.8.8.8

    Returns:
        str: host ping output
    """
    host_stats = ping(host, '-c 3', 'grep %')
    if host_stats is None:
        logging.error('Host ping is None')
        sleep(5)
        host_stats = host_ping(host)
    return host_stats


def host_received(host: str) -> int:
    """cheks `host_ping` and filtered number of received packages

    Args:
        host (str): 8.8.8.8

    Returns:
        int: number of received packages
    """
    host_stats = host_ping(host)
    received = int(''.join(filter(str.isdigit, host_stats.split(',')[1])))
    return received


def monitoring(selected_ip: str, host: str, hotspot: str) -> None:
    """main function. collect data and restart Wi-Fi or network when needed

    Args:
        selected_ip (str): ip with min avg ping
        host (str): 8.8.8.8
        hotspot (str): name wifi conection
    """
    while True:
        avg_local, selected_ip = local_avg(selected_ip)
        received = host_received(host)
        if avg_local > 100:
            logging.warning(f'Local ping avg > 100: {avg_local}')
            new_ip = select_ip()
            if new_ip == selected_ip:
                reboot_wifi(hotspot)
            else:
                selected_ip = new_ip
                logging.warning(f'Local ip chenged: {selected_ip}')
                continue
        if received < 2:
            reboot_networking()
            reboot_wifi(hotspot)
        sleep(5)


if __name__ == "__main__":
    file_dir = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig(
        filename=f'{file_dir}/network_monitoring.log',
        format='%(asctime)s %(levelname)s:%(message)s',
        level=logging.INFO
        )
    logging.info('Started session')
    host = '8.8.8.8'
    selected_ip = select_ip()
    hotspot = select_hotspot()
    monitoring(selected_ip, host, hotspot)
    logging.info('Stoped session')
