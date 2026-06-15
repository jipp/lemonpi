#!/usr/bin/env python3

import configparser
import argparse
import glob
import shlex
import shutil
import subprocess
import sys
import os

verbose = False

def main():
  global verbose

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="tool to maintain the system",
    usage='%(prog)s [options]',
    epilog='''examples:
  %(prog)s -s update                  system update
  %(prog)s -d "ps -a"                 docker compose ps -a
  %(prog)s -d prune                   docker system prune
  %(prog)s -c "renew --dry-run"       certbot dry run
  %(prog)s -e "run config.yaml"       esphome run
  %(prog)s -m "say hello"             minecraft rcon command
  %(prog)s -b execute                 backup all apps
  %(prog)s -b execute nginx           backup single app
  %(prog)s -b local                   copy backups to local mount
  %(prog)s -b remote                  copy backups to remote server'''
  )

  script_dir = os.path.dirname(os.path.abspath(__file__))
  default_file = os.path.join(script_dir, 'tools.ini')

  parser.add_argument('-b', '--backup', nargs='+', help='<command> <app> <app>')
  parser.add_argument('-c', '--certbot', nargs='+', help='example: "renew --dry-run"')
  parser.add_argument('-d', '--docker', nargs='+')
  parser.add_argument('-e', '--esphome', nargs='+', help='<command> <yaml-file>')
  parser.add_argument('-f', '--file', default=default_file, help='config file')
  parser.add_argument('-m', '--minecraft', nargs='+')
  parser.add_argument('-s', '--system', choices=['health', 'info', 'update'])
  parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
  parser.add_argument('-V', '--verbose', action='store_true', help='show executed commands')

  args = parser.parse_args()

  if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(0)

  verbose = args.verbose

  config = configparser.ConfigParser()

  if os.path.exists(args.file):
    config.read(args.file)
  else:
    create_default_config(args.file, config)

  if args.system is not None:
    require_section(config, 'system')
    require_keys(config, 'system', args.system)
    run_system(args.system, config)
  if args.certbot is not None:
    require_section(config, 'docker')
    require_keys(config, 'docker', 'folder')
    require_docker()
    run_certbot(config, args.certbot)
  if args.esphome is not None:
    require_section(config, 'docker', 'esphome')
    require_keys(config, 'docker', 'folder')
    require_keys(config, 'esphome', 'folder')
    require_docker()
    run_esphome(config, args.esphome)
  if args.docker is not None:
    require_section(config, 'docker')
    require_keys(config, 'docker', 'folder')
    require_docker()
    run_docker(config, args.docker)
  if args.minecraft is not None:
    require_section(config, 'minecraft')
    require_keys(config, 'minecraft', 'identifier')
    require_docker()
    run_minecraft(config, args.minecraft)
  if args.backup is not None:
    require_section(config, 'backup', 'local', 'remote', 'settings')
    require_keys(config, 'backup', 'src', 'dst', 'apps')
    require_keys(config, 'local', 'user', 'server', 'port', 'mnt', 'dst')
    require_keys(config, 'remote', 'user', 'server', 'port', 'dst')
    require_keys(config, 'settings', 'files', 'bkp')
    run_backup(config, args.backup)


def require_section(config, *sections):
  for section in sections:
    if section not in config:
      print(f"Error: section [{section}] missing in config file", file=sys.stderr)
      sys.exit(1)


def require_keys(config, section, *keys):
  for key in keys:
    if key not in config[section]:
      print(f"Error: key '{key}' missing in section [{section}]", file=sys.stderr)
      sys.exit(1)


def require_docker():
  if shutil.which("docker") is None:
    print("Error: docker is not installed or not in PATH", file=sys.stderr)
    sys.exit(1)


def create_default_config(path, config):
  config['system'] = {
    'update': 'sudo apt update && sudo apt list --upgradable && sudo apt upgrade && sudo apt autoremove -y',
    'health': 'dmesg -e -l emerg --level=alert,crit,err,warn,notice',
    'info': 'uname -a && uptime && df -h && sudo rpi-eeprom-update',
  }
  config['docker'] = {'folder': '/home/woke/lemonpi/docker'}
  config['esphome'] = {'folder': '/home/woke/lemonpi/esphome'}
  config['minecraft'] = {'identifier': 'minecraft-server'}
  config['backup'] = {
    'src': '/docker',
    'dst': '/backup',
    'apps': 'certbot homeassistant nginx octoprint minecraft-server minecraft-server-small',
  }
  config['local'] = {
    'user': 'woke',
    'server': 'localhost',
    'port': '22',
    'mnt': '/mnt',
    'dst': '/mnt/lemonpi',
  }
  config['remote'] = {
    'user': 'wolfgang.keller',
    'server': 'ds416play',
    'port': '221',
    'dst': 'lemonpi',
  }
  config['settings'] = {'files': '.ssh .gitconfig', 'bkp': 'settings.tgz'}
  with open(path, 'w') as f:
    config.write(f)


def split_args(cmd):
  return [arg for c in cmd for arg in shlex.split(c)]


def run(cmd, **kwargs):
  if verbose:
    display = ' '.join(cmd) if isinstance(cmd, list) else cmd
    print(f"  > {display}", file=sys.stderr)
  result = subprocess.run(cmd, **kwargs)
  if result.returncode != 0:
    print(f"Error: {' '.join(cmd) if isinstance(cmd, list) else cmd}", file=sys.stderr)
    sys.exit(result.returncode)


def run_system(cmd, config):
  run(config['system'][cmd], shell=True)


def run_certbot(config, cmd):
  folder = config['docker']['folder']
  cmd = split_args(cmd)
  run(["docker", "compose", "run", "--rm", "-p", "8080:80", "certbot"] + cmd, cwd=folder)
  run(["docker", "compose", "exec", "nginx", "nginx", "-s", "reload"], cwd=folder)
  run(["docker", "compose", "down", "certbot"], cwd=folder)


def run_esphome(config, cmd):
  folder = config['docker']['folder']
  esphome_folder = config['esphome']['folder']
  cmd = split_args(cmd)
  run(["docker", "compose", "--project-directory", folder, "run", "--rm", "esphome"] + cmd, cwd=esphome_folder)


def run_docker(config, cmd):
  folder = config['docker']['folder']
  cmd = split_args(cmd)
  match cmd[0]:
    case "prune":
      run(["docker", "system", "prune", "-f"] + cmd[1:])
    case "pull":
      run(["docker", "compose", "--profile", "manual"] + cmd, cwd=folder)
    case _:
      run(["docker", "compose"] + cmd, cwd=folder)


def run_minecraft(config, cmd):
  identifier = config['minecraft']['identifier']
  cmd = split_args(cmd)
  result = subprocess.run(
    ["docker", "ps", "-a", "--filter", "status=running", "--format", "{{.Names}}", "--filter", f"name={identifier}"],
    capture_output=True, text=True
  )
  servers = result.stdout.split()
  for server in servers:
    print(f"{server}:")
    run(["docker", "exec", server, "rcon-cli"] + cmd)


def run_backup(config, cmd):
  backup = config['backup']
  local = config['local']
  remote = config['remote']
  settings = config['settings']

  cmd = split_args(cmd)

  valid_commands = ('execute', 'settings', 'local', 'remote', 'list')
  if cmd[0] not in valid_commands:
    print(f"Error: unknown backup command '{cmd[0]}'. Allowed: {', '.join(valid_commands)}", file=sys.stderr)
    sys.exit(1)

  apps = backup['apps'].split() if len(cmd) == 1 else cmd[1:]

  match cmd[0]:
    case 'execute':
      if not os.path.isdir(backup['dst']):
        print(f"dst folder does not exist: {backup['dst']}", file=sys.stderr)
        sys.exit(1)
      ok, skipped = 0, 0
      for app in apps:
        print(f"{app:25}", end="", flush=True)
        src_path = os.path.join(backup['src'], app)
        if not os.path.isdir(src_path):
          print("app does not exist")
          skipped += 1
          continue
        result = subprocess.run(
          ["sudo", "tar", "czf", os.path.join(backup['dst'], f"{app}.tgz"), app],
          cwd=backup['src'], capture_output=True
        )
        if result.returncode == 0:
          print("ok")
          ok += 1
        else:
          print("app modified during archiving")
          ok += 1
      print(f"\n{ok}/{ok + skipped} apps backed up, {skipped} skipped")

    case 'settings':
      if not os.path.isdir(backup['dst']):
        print(f"dst folder does not exist: {backup['dst']}", file=sys.stderr)
        sys.exit(1)
      home = os.path.expanduser("~")
      result = subprocess.run(
        ["sudo", "tar", "czf", os.path.join(backup['dst'], settings['bkp'])] + settings['files'].split(),
        cwd=home, capture_output=True
      )
      if result.returncode != 0:
        print("Error backing up settings", file=sys.stderr)
        sys.exit(1)

    case 'local':
      if not os.path.ismount(local['mnt']):
        print(f"Error: {local['mnt']} not mounted", file=sys.stderr)
        sys.exit(1)
      if not os.path.exists(local['dst']):
        print(f"Error: {local['dst']} does not exist", file=sys.stderr)
        sys.exit(1)
      files = glob.glob(os.path.join(backup['dst'], '*'))
      if files:
        run(["scp", "-P", local['port'], "-O"] + files + [f"{local['user']}@{local['server']}:{local['dst']}/"])

    case 'remote':
      result = subprocess.run(["ping", "-c", "1", "-w", "1", remote['server']], capture_output=True)
      if result.returncode != 0:
        print(f"Error: {remote['server']} not reachable", file=sys.stderr)
        sys.exit(1)
      files = glob.glob(os.path.join(backup['dst'], '*'))
      if files:
        run(["scp", "-P", remote['port'], "-O"] + files + [f"{remote['user']}@{remote['server']}:{remote['dst']}/"])

    case 'list':
      run(["ls", "-lh", backup['dst']])


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\nAborted.", file=sys.stderr)
    sys.exit(130)
