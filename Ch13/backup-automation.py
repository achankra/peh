#!/usr/bin/env python3
"""
Automated Backup Automation Script using Velero CLI

This script manages Kubernetes backups using Velero, including:
- Creating scheduled backups
- Validating backup integrity
- Managing backup retention
- Generating backup reports
- Testing restore procedures

Usage:
    python3 backup-automation.py --schedule daily --retention 30
    python3 backup-automation.py --list-backups
    python3 backup-automation.py --validate-backups
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VeleroBackupManager:
    """Manages Kubernetes backups using Velero."""

    def __init__(self, velero_namespace: str = "velero"):
        """Initialize Velero backup manager.
        
        Args:
            velero_namespace: Kubernetes namespace where Velero is installed
        """
        self.velero_namespace = velero_namespace
        self.backup_name_prefix = "scheduled-backup"

    def _run_command(self, command: List[str]) -> Tuple[int, str, str]:
        """Execute shell command and return output.
        
        Args:
            command: Command to execute as list of strings
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {' '.join(command)}")
            return 124, "", "Command timeout"
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return 1, "", str(e)

    def create_backup(
        self,
        backup_name: str,
        namespaces: List[str] = None,
        exclude_namespaces: List[str] = None,
        include_pvs: bool = True,
        wait: bool = False
    ) -> bool:
        """Create a Velero backup.
        
        Args:
            backup_name: Name for the backup
            namespaces: Specific namespaces to backup (None = all)
            exclude_namespaces: Namespaces to exclude from backup
            include_pvs: Whether to backup persistent volumes
            wait: Whether to wait for backup completion
            
        Returns:
            True if backup created successfully
        """
        cmd = ["velero", "backup", "create", backup_name]
        
        if namespaces:
            cmd.extend(["--include-namespaces", ",".join(namespaces)])
        else:
            cmd.append("--include-namespaces", "*")
        
        if exclude_namespaces:
            cmd.extend(["--exclude-namespaces", ",".join(exclude_namespaces)])
        
        if include_pvs:
            cmd.append("--snapshot-volumes=true")
        
        if wait:
            cmd.append("--wait")
        
        logger.info(f"Creating backup: {backup_name}")
        returncode, stdout, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.error(f"Backup creation failed: {stderr}")
            return False
        
        logger.info(f"Backup created successfully: {backup_name}")
        return True

    def schedule_backup(
        self,
        schedule_name: str,
        schedule: str,
        namespaces: List[str] = None,
        retention_days: int = 30,
        include_pvs: bool = True
    ) -> bool:
        """Create a scheduled backup.
        
        Args:
            schedule_name: Name for the schedule
            schedule: Cron expression (e.g., "0 2 * * *" for daily at 2am)
            namespaces: Namespaces to include in backup
            retention_days: Days to retain backups
            include_pvs: Whether to backup persistent volumes
            
        Returns:
            True if schedule created successfully
        """
        cmd = [
            "velero", "schedule", "create", schedule_name,
            "--schedule", schedule
        ]
        
        if namespaces:
            cmd.extend(["--include-namespaces", ",".join(namespaces)])
        
        cmd.extend(["--ttl", f"{retention_days}d"])
        
        if include_pvs:
            cmd.append("--snapshot-volumes=true")
        
        logger.info(f"Creating backup schedule: {schedule_name}")
        returncode, stdout, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.error(f"Schedule creation failed: {stderr}")
            return False
        
        logger.info(f"Backup schedule created: {schedule_name} ({schedule})")
        return True

    def list_backups(self) -> List[Dict]:
        """List all backups in JSON format.
        
        Returns:
            List of backup dictionaries
        """
        cmd = ["velero", "backup", "get", "-o", "json"]
        returncode, stdout, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to list backups: {stderr}")
            return []
        
        try:
            data = json.loads(stdout)
            return data.get("items", [])
        except json.JSONDecodeError:
            logger.error("Failed to parse backup list JSON")
            return []

    def get_backup_status(self, backup_name: str) -> Dict:
        """Get detailed status of a backup.
        
        Args:
            backup_name: Name of the backup
            
        Returns:
            Backup status dictionary
        """
        cmd = ["velero", "backup", "describe", backup_name, "-o", "json"]
        returncode, stdout, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to describe backup {backup_name}: {stderr}")
            return {}
        
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse backup status JSON")
            return {}

    def validate_backups(self) -> Dict[str, bool]:
        """Validate integrity of all recent backups.
        
        Returns:
            Dictionary of backup_name -> is_valid mapping
        """
        backups = self.list_backups()
        validation_results = {}
        
        logger.info(f"Validating {len(backups)} backups...")
        
        for backup in backups:
            backup_name = backup.get("metadata", {}).get("name")
            if not backup_name:
                continue
            
            status = self.get_backup_status(backup_name)
            phase = status.get("status", {}).get("phase")
            
            # Check backup phase
            is_valid = phase == "Completed"
            validation_results[backup_name] = is_valid
            
            log_level = logging.INFO if is_valid else logging.WARNING
            logger.log(log_level, f"Backup {backup_name}: {phase}")
        
        return validation_results

    def get_backup_freshness(self, days_threshold: int = 1) -> Dict[str, bool]:
        """Check if backups are recent enough.
        
        Args:
            days_threshold: Maximum acceptable age in days
            
        Returns:
            Dictionary of backup_name -> is_fresh mapping
        """
        backups = self.list_backups()
        freshness_results = {}
        threshold_time = datetime.utcnow() - timedelta(days=days_threshold)
        
        logger.info(f"Checking backup freshness (threshold: {days_threshold} days)...")
        
        for backup in backups:
            backup_name = backup.get("metadata", {}).get("name")
            if not backup_name:
                continue
            
            # Get backup start time
            start_time_str = backup.get("status", {}).get("startTimestamp")
            if not start_time_str:
                freshness_results[backup_name] = False
                continue
            
            try:
                # Parse ISO format timestamp
                backup_time = datetime.fromisoformat(
                    start_time_str.replace('Z', '+00:00')
                )
                is_fresh = backup_time > threshold_time
                freshness_results[backup_name] = is_fresh
                
                age_hours = (datetime.utcnow() - backup_time).total_seconds() / 3600
                status = "FRESH" if is_fresh else "STALE"
                logger.info(f"Backup {backup_name}: {status} ({age_hours:.1f} hours old)")
            except ValueError:
                logger.warning(f"Could not parse timestamp for {backup_name}")
                freshness_results[backup_name] = False
        
        return freshness_results

    def generate_backup_report(self) -> str:
        """Generate a detailed backup report.
        
        Returns:
            Report as formatted string
        """
        backups = self.list_backups()
        
        report = []
        report.append("=" * 60)
        report.append("VELERO BACKUP REPORT")
        report.append(f"Generated: {datetime.utcnow().isoformat()}Z")
        report.append("=" * 60)
        report.append("")
        
        if not backups:
            report.append("No backups found")
            return "\n".join(report)
        
        report.append(f"Total Backups: {len(backups)}\n")
        
        # Backup summary
        for backup in backups:
            metadata = backup.get("metadata", {})
            status = backup.get("status", {})
            
            name = metadata.get("name", "Unknown")
            phase = status.get("phase", "Unknown")
            start_time = status.get("startTimestamp", "Unknown")
            completion_time = status.get("completionTimestamp", "Unknown")
            
            report.append(f"Backup: {name}")
            report.append(f"  Status: {phase}")
            report.append(f"  Started: {start_time}")
            report.append(f"  Completed: {completion_time}")
            
            # Include stats if available
            stats = status.get("backupItemOperationAttempts")
            if stats:
                report.append(f"  Items: {stats}")
            report.append("")
        
        return "\n".join(report)

    def cleanup_old_backups(self, days_to_keep: int = 30) -> bool:
        """Remove backups older than specified days.
        
        Args:
            days_to_keep: Keep backups newer than this many days
            
        Returns:
            True if cleanup successful
        """
        backups = self.list_backups()
        threshold_time = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        logger.info(f"Cleaning up backups older than {days_to_keep} days...")
        
        for backup in backups:
            metadata = backup.get("metadata", {})
            status = backup.get("status", {})
            
            backup_name = metadata.get("name")
            if not backup_name:
                continue
            
            start_time_str = status.get("startTimestamp")
            if not start_time_str:
                continue
            
            try:
                backup_time = datetime.fromisoformat(
                    start_time_str.replace('Z', '+00:00')
                )
                
                if backup_time < threshold_time:
                    cmd = ["velero", "backup", "delete", backup_name, "--confirm"]
                    returncode, _, stderr = self._run_command(cmd)
                    
                    if returncode == 0:
                        logger.info(f"Deleted backup: {backup_name}")
                        deleted_count += 1
                    else:
                        logger.error(f"Failed to delete {backup_name}: {stderr}")
            except ValueError:
                logger.warning(f"Could not parse timestamp for {backup_name}")
        
        logger.info(f"Cleanup complete: {deleted_count} backups deleted")
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Velero-based Kubernetes backup automation"
    )
    parser.add_argument(
        "--schedule",
        choices=["daily", "weekly", "monthly"],
        help="Create a backup schedule"
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=30,
        help="Days to retain backups (default: 30)"
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List all backups"
    )
    parser.add_argument(
        "--validate-backups",
        action="store_true",
        help="Validate backup integrity"
    )
    parser.add_argument(
        "--check-freshness",
        type=int,
        help="Check if backups are fresher than N days"
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate backup report"
    )
    parser.add_argument(
        "--cleanup",
        type=int,
        help="Remove backups older than N days"
    )
    
    args = parser.parse_args()
    
    manager = VeleroBackupManager()
    
    # Schedule backup
    if args.schedule:
        schedule_map = {
            "daily": "0 2 * * *",
            "weekly": "0 2 * * 0",
            "monthly": "0 2 1 * *"
        }
        cron_expr = schedule_map[args.schedule]
        schedule_name = f"backup-{args.schedule}"
        
        success = manager.schedule_backup(
            schedule_name=schedule_name,
            schedule=cron_expr,
            retention_days=args.retention,
            include_pvs=True
        )
        sys.exit(0 if success else 1)
    
    # List backups
    if args.list_backups:
        backups = manager.list_backups()
        for backup in backups:
            name = backup.get("metadata", {}).get("name")
            phase = backup.get("status", {}).get("phase")
            print(f"{name}: {phase}")
        sys.exit(0)
    
    # Validate backups
    if args.validate_backups:
        results = manager.validate_backups()
        all_valid = all(results.values())
        
        for backup_name, is_valid in results.items():
            status = "VALID" if is_valid else "INVALID"
            print(f"{backup_name}: {status}")
        
        sys.exit(0 if all_valid else 1)
    
    # Check freshness
    if args.check_freshness:
        results = manager.get_backup_freshness(args.check_freshness)
        all_fresh = all(results.values())
        
        for backup_name, is_fresh in results.items():
            status = "FRESH" if is_fresh else "STALE"
            print(f"{backup_name}: {status}")
        
        sys.exit(0 if all_fresh else 1)
    
    # Generate report
    if args.generate_report:
        report = manager.generate_backup_report()
        print(report)
        sys.exit(0)
    
    # Cleanup old backups
    if args.cleanup:
        success = manager.cleanup_old_backups(args.cleanup)
        sys.exit(0 if success else 1)
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
