#!/usr/bin/env python
import argparse
import os
import sys
import subprocess

# Ajout du répertoire parent au chemin pour pouvoir importer les modules du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_args():
    parser = argparse.ArgumentParser(description='Database migration script')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Commande migrate
    migrate_parser = subparsers.add_parser('migrate', help='Run migrations')
    migrate_parser.add_argument('--revision', '-r', help='Revision to migrate to')
    
    # Commande rollback
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migrations')
    rollback_parser.add_argument('--revision', '-r', help='Revision to rollback to')
    
    # Commande create
    create_parser = subparsers.add_parser('create', help='Create a new migration')
    create_parser.add_argument('--message', '-m', required=True, help='Migration message')
    
    # Commande init
    subparsers.add_parser('init', help='Initialize the database')
    
    # Commande seed
    subparsers.add_parser('seed', help='Seed the database with initial data')
    
    # Commande reset
    subparsers.add_parser('reset', help='Reset the database')
    
    return parser.parse_args()

def run_command(command):
    process = subprocess.Popen(command, shell=True)
    return process.wait()

def main():
    args = parse_args()
    
    if args.command == 'migrate':
        if args.revision:
            cmd = f'alembic upgrade {args.revision}'
        else:
            cmd = 'alembic upgrade head'
        print(f'Running: {cmd}')
        return run_command(cmd)
    
    elif args.command == 'rollback':
        if args.revision:
            cmd = f'alembic downgrade {args.revision}'
        else:
            cmd = 'alembic downgrade -1'
        print(f'Running: {cmd}')
        return run_command(cmd)
    
    elif args.command == 'create':
        cmd = f'alembic revision --autogenerate -m "{args.message}"'
        print(f'Running: {cmd}')
        return run_command(cmd)
    
    elif args.command == 'init':
        cmd = 'alembic upgrade 20250224_initial'
        print(f'Running: {cmd}')
        return run_command(cmd)
    
    elif args.command == 'seed':
        cmd = 'alembic upgrade 20250224_seed_data'
        print(f'Running: {cmd}')
        return run_command(cmd)
    
    elif args.command == 'reset':
        cmd = 'alembic downgrade base && alembic upgrade head'
        print(f'Running: {cmd}')
        return run_command(cmd)
    
    else:
        print('Unknown command. Use --help for usage info.')
        return 1

if __name__ == '__main__':
    sys.exit(main())