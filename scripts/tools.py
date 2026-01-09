#!/usr/bin/env python3

import configparser
import argparse
import subprocess
import os

def main():
  parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description="tool to maintain the system",
    usage='%(prog)s [options]',
    epilog='this is work in progress'
  )

  parser.add_argument('-b', '--backup', nargs='+', help='<command> <app> <app>')
  parser.add_argument('-c', '--certbot', nargs='+', help='example: \"renew --dry-run\"')
  parser.add_argument('-d', '--docker', nargs='+')
  parser.add_argument('-e', '--esphome', nargs='+', help='<command> <yaml-file>')
  parser.add_argument('-f', '--file', nargs=1, default='tools.ini', help='config file')
  parser.add_argument('-m', '--minecraft', nargs='+')
  parser.add_argument('-s', '--system', choices=['health', 'info', 'update'])
  parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')

  args = parser.parse_args()

  config = configparser.ConfigParser()

  if os.path.exists(args.file):
    config.read(args.file)
  else:
    config['system'] = {}
    config['system']['update'] = 'sudo apt update && sudo apt list --upgradable && sudo apt upgrade && sudo apt autoremove -y'
    config['system']['health'] = 'dmesg -e -l emerg --level=alert,crit,err,warn,notice'
    config['system']['info'] = 'uname -a && uptime && df -h'
    config['docker'] = {}
    config['docker']['folder'] = '/home/woke/lemonpi/docker'
    config['esphome'] = {}
    config['esphome']['folder'] = '/home/woke/lemonpi/esphome'
    config['minecraft'] = {}
    config['minecraft']['identifier'] = 'minecraft-server'
    config['backup'] = {}
    config['backup']['src'] = '/docker'
    config['backup']['dst'] = '/backup'
    config['backup']['apps'] = 'certbot homeassistant nginx octoprint minecraft-server minecraft-server-small'
    config['local'] = {}
    config['local']['user'] = 'woke'
    config['local']['server'] = 'localhost'
    config['local']['port'] = '22'
    config['local']['mnt'] = '/mnt'
    config['local']['dst'] = '/mnt/lemonpi'
    config['remote'] = {}
    config['remote']['user'] = 'wolfgang.keller'
    config['remote']['server'] = 'ds416play'
    config['remote']['port'] = '221'
    config['remote']['dst'] = 'lemonpi'
    config['settings'] = {}
    config['settings']['files'] = '.ssh .gitconfig'
    config['settings']['bkp'] = 'settings.tgz'
    config.write(open(args.file, 'w'))

  system = {
    'health': config['system']['health'],
    'info': config['system']['info'],
    'update': config['system']['update'],
  }
  docker = {
    'folder': config['docker']['folder']
  }
  esphome = {
    'folder': config['esphome']['folder']
  }
  minecraft = {
    'identifier': config['minecraft']['identifier']
  }
  backup = {
    'src': config['backup']['src'],
    'dst': config['backup']['dst'],
    'apps': config['backup']['apps']
  }
  remote = {
    'user': config['remote']['user'],
    'server': config['remote']['server'],
    'port': config['remote']['port'],
    'dst': config['remote']['dst']
  }
  local = {
    'user': config['local']['user'],
    'server': config['local']['server'],
    'port': config['local']['port'],
    'mnt': config['local']['mnt'],
    'dst': config['local']['dst']
  } 
  settings = {
    'files': config['settings']['files'],
    'bkp': config['settings']['bkp']
  }


  if args.system != None:
    run_system(args.system, system)

  if args.certbot != None:
    run_certbot(docker, args.certbot)

  if args.esphome != None:
    run_esphome(esphome, docker, args.esphome)

  if args.docker != None:
    run_docker(docker, args.docker)

  if args.minecraft != None:
    run_minecraft(minecraft, args.minecraft)

  if args.backup != None:
    run_backup(backup, local, remote, settings, args.backup)

  return

def run_system(cmd, system):
  os.system(system[cmd])

def run_certbot(docker, cmd):
  os.system("cd "+docker['folder']+" && docker compose run --rm -p 8080:80 certbot "+' '.join(cmd))
  os.system("cd "+docker['folder']+" && docker compose exec -it nginx nginx -s reload")
  os.system("cd "+docker['folder']+" && docker compose down certbot")

def run_esphome(esphome, docker, cmd):
  os.system("cd "+esphome['folder']+" && docker compose --project-directory "+docker['folder']+" run --rm esphome "+' '.join(cmd))

def run_docker(docker, cmd):
  match cmd[0]:
    case "prune":
      os.system("docker system prune -f")
    case "pull":
      os.system("cd "+docker['folder']+" && docker compose --profile manual "+' '.join(cmd))
    case _:
      os.system("cd "+docker['folder']+" && docker compose "+' '.join(cmd))

def run_minecraft(minecraft, cmd):
  servers = subprocess.run(["docker ps -a --filter status=running --format {{.Names}} --filter name="+minecraft['identifier']], shell=True, capture_output=True, text=True).stdout.split()
  for server in servers:
    print(server+":")
    os.system("docker exec -it "+server+" rcon-cli "+' '.join(cmd))

def run_backup(backup, local, remote, settings, cmd):
  if len(cmd) == 1:
    apps = backup['apps'].split()
  else:
    apps = cmd.copy()
    apps.pop(0)
  match cmd[0]:
    case 'execute':
      if not os.path.isdir(backup['dst']):
        print("dst folder does not exist: "+backup['dst'])
        exit(1)
      for app in apps:
        print(f"{app:25}", end="", flush=True)
        try:
          if not os.path.isdir(backup['src']+"/"+app):
            raise Exception("app does not exist")
          if os.system("cd "+backup['src']+" && sudo tar czf "+backup['dst']+"/"+app+".tgz "+app+" >/dev/null 2>&1") != 0:
            raise Exception("app modified during archiveing")
        except Exception as e:
          print(e)
        else:
          print("ok")
    case 'settings':
      if not os.path.isdir(backup['dst']):
        print("dst folder does not exist: "+backup['dst'])
        exit(1)
      if os.system("cd && sudo tar czf "+backup['dst']+"/"+settings['bkp']+" "+settings['files']+" >/dev/null 2>&1") != 0:
        raise Exception("app modified during archiveing")
    case 'local':
      if os.path.ismount(local['mnt']):
        if os.path.exists(local['dst']):
          os.system("scp -P "+local['port']+" -O "+backup['dst']+"/* "+local['user']+"@"+local['server']+":"+local['dst']+"/")
        else:
          print(local['dst']+" does not exist")
      else:
        print(local['mnt']+ " not mounted")
    case 'remote':
      if os.system("ping -c 1 -w 1 "+remote['server']+" >/dev/null 2>&1") == 0:
        os.system("scp -P "+remote['port']+" -O "+backup['dst']+"/* "+remote['user']+"@"+remote['server']+":"+remote['dst']+"/")
      else:
        print(remote['server']+" seems not reachable")
    case 'list':
      os.system("ls -lh "+backup['dst'])

if __name__ == "__main__":
  main()
