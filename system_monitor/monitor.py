#!/usr/bin/env python3
"""
System Resource Monitoring System
Monitors CPU, Memory, Disk, Network, and Temperature in real-time
"""

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend

import psutil
import time
import json
import os
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

class SystemMonitor:
    def __init__(self, duration=300, interval=2):
        """
        Initialize System Monitor

        Args:
            duration: Monitoring duration in seconds (default: 300 = 5 minutes)
            interval: Data collection interval in seconds (default: 2)
        """
        self.duration = duration
        self.interval = interval
        self.start_time = None
        self.data = {
            'timestamps': [],
            'cpu_percent': [],
            'cpu_per_core': [],
            'memory_percent': [],
            'memory_used': [],
            'memory_available': [],
            'disk_usage': [],
            'disk_read': [],
            'disk_write': [],
            'network_sent': [],
            'network_recv': [],
            'temperatures': []
        }

        # For real-time plotting (keep last 60 points)
        self.max_points = 60
        self.time_data = deque(maxlen=self.max_points)
        self.cpu_data = deque(maxlen=self.max_points)
        self.mem_data = deque(maxlen=self.max_points)
        self.net_sent_data = deque(maxlen=self.max_points)
        self.net_recv_data = deque(maxlen=self.max_points)

        # Network baseline
        self.net_io_start = psutil.net_io_counters()
        self.disk_io_start = psutil.disk_io_counters()

    def collect_cpu_info(self):
        """Collect CPU usage information"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        return cpu_percent, cpu_per_core

    def collect_memory_info(self):
        """Collect memory usage information"""
        mem = psutil.virtual_memory()
        return {
            'percent': mem.percent,
            'used': mem.used / (1024**3),  # GB
            'available': mem.available / (1024**3),  # GB
            'total': mem.total / (1024**3)  # GB
        }

    def collect_disk_info(self):
        """Collect disk usage information"""
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        # Calculate delta
        if disk_io and self.disk_io_start:
            read_mb = (disk_io.read_bytes - self.disk_io_start.read_bytes) / (1024**2)
            write_mb = (disk_io.write_bytes - self.disk_io_start.write_bytes) / (1024**2)
        else:
            read_mb = 0
            write_mb = 0

        return {
            'percent': disk.percent,
            'read_mb': read_mb,
            'write_mb': write_mb
        }

    def collect_network_info(self):
        """Collect network traffic information"""
        net_io = psutil.net_io_counters()

        # Calculate delta from start
        sent_mb = (net_io.bytes_sent - self.net_io_start.bytes_sent) / (1024**2)
        recv_mb = (net_io.bytes_recv - self.net_io_start.bytes_recv) / (1024**2)

        return {
            'sent_mb': sent_mb,
            'recv_mb': recv_mb
        }

    def collect_temperature_info(self):
        """Collect temperature sensor information"""
        temps = {}
        try:
            temps_dict = psutil.sensors_temperatures()
            if temps_dict:
                for name, entries in temps_dict.items():
                    for entry in entries:
                        temps[f"{name}_{entry.label}"] = entry.current
            else:
                temps['note'] = 'Temperature sensors not available'
        except AttributeError:
            temps['note'] = 'Temperature monitoring not supported on this platform'

        return temps

    def collect_all_data(self):
        """Collect all system metrics"""
        timestamp = time.time() - self.start_time

        cpu_percent, cpu_per_core = self.collect_cpu_info()
        memory = self.collect_memory_info()
        disk = self.collect_disk_info()
        network = self.collect_network_info()
        temps = self.collect_temperature_info()

        # Store in history
        self.data['timestamps'].append(timestamp)
        self.data['cpu_percent'].append(cpu_percent)
        self.data['cpu_per_core'].append(cpu_per_core)
        self.data['memory_percent'].append(memory['percent'])
        self.data['memory_used'].append(memory['used'])
        self.data['memory_available'].append(memory['available'])
        self.data['disk_usage'].append(disk['percent'])
        self.data['disk_read'].append(disk['read_mb'])
        self.data['disk_write'].append(disk['write_mb'])
        self.data['network_sent'].append(network['sent_mb'])
        self.data['network_recv'].append(network['recv_mb'])
        self.data['temperatures'].append(temps)

        # Store in deque for real-time plotting
        self.time_data.append(timestamp)
        self.cpu_data.append(cpu_percent)
        self.mem_data.append(memory['percent'])
        self.net_sent_data.append(network['sent_mb'])
        self.net_recv_data.append(network['recv_mb'])

        return {
            'timestamp': timestamp,
            'cpu': cpu_percent,
            'memory': memory['percent'],
            'network_sent': network['sent_mb'],
            'network_recv': network['recv_mb']
        }

    def save_data(self):
        """Save collected data to JSON file"""
        output_file = 'data/monitoring_data.json'
        os.makedirs('data', exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=2)

        print(f"\nData saved to {output_file}")
        return output_file

    def setup_realtime_plot(self):
        """Setup real-time plotting figure"""
        plt.style.use('seaborn-v0_8-darkgrid')
        self.fig = plt.figure(figsize=(15, 10))
        self.fig.suptitle('Real-Time System Resource Monitoring', fontsize=16, fontweight='bold')

        gs = GridSpec(3, 2, figure=self.fig, hspace=0.3, wspace=0.3)

        self.ax1 = self.fig.add_subplot(gs[0, 0])  # CPU
        self.ax2 = self.fig.add_subplot(gs[0, 1])  # Memory
        self.ax3 = self.fig.add_subplot(gs[1, 0])  # Network Sent
        self.ax4 = self.fig.add_subplot(gs[1, 1])  # Network Recv
        self.ax5 = self.fig.add_subplot(gs[2, :])  # Combined view

        # Setup axes
        self.ax1.set_title('CPU Usage (%)', fontweight='bold')
        self.ax1.set_ylim(0, 100)
        self.ax1.set_ylabel('Percentage')

        self.ax2.set_title('Memory Usage (%)', fontweight='bold')
        self.ax2.set_ylim(0, 100)
        self.ax2.set_ylabel('Percentage')

        self.ax3.set_title('Network Sent (MB)', fontweight='bold')
        self.ax3.set_ylabel('MB')

        self.ax4.set_title('Network Received (MB)', fontweight='bold')
        self.ax4.set_ylabel('MB')

        self.ax5.set_title('Combined CPU & Memory Usage', fontweight='bold')
        self.ax5.set_ylim(0, 100)
        self.ax5.set_ylabel('Percentage')
        self.ax5.set_xlabel('Time (seconds)')

        # Lines
        self.line1, = self.ax1.plot([], [], 'r-', linewidth=2, label='CPU')
        self.line2, = self.ax2.plot([], [], 'b-', linewidth=2, label='Memory')
        self.line3, = self.ax3.plot([], [], 'g-', linewidth=2, label='Sent')
        self.line4, = self.ax4.plot([], [], 'm-', linewidth=2, label='Received')
        self.line5, = self.ax5.plot([], [], 'r-', linewidth=2, label='CPU', alpha=0.7)
        self.line6, = self.ax5.plot([], [], 'b-', linewidth=2, label='Memory', alpha=0.7)

        self.ax1.legend(loc='upper right')
        self.ax2.legend(loc='upper right')
        self.ax3.legend(loc='upper right')
        self.ax4.legend(loc='upper right')
        self.ax5.legend(loc='upper right')

        self.ax1.grid(True, alpha=0.3)
        self.ax2.grid(True, alpha=0.3)
        self.ax3.grid(True, alpha=0.3)
        self.ax4.grid(True, alpha=0.3)
        self.ax5.grid(True, alpha=0.3)

    def update_realtime_graph(self, current_data):
        """Update and save real-time monitoring graph"""
        times = list(self.time_data)

        if not times:
            return

        # Clear all axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.ax5.clear()

        # Plot CPU
        self.ax1.plot(times, list(self.cpu_data), 'r-', linewidth=2, label='CPU')
        self.ax1.fill_between(times, list(self.cpu_data), alpha=0.3, color='red')
        self.ax1.set_title('CPU Usage (%)', fontweight='bold')
        self.ax1.set_ylim(0, 100)
        self.ax1.set_ylabel('Percentage')
        self.ax1.legend(loc='upper right')
        self.ax1.grid(True, alpha=0.3)

        # Plot Memory
        self.ax2.plot(times, list(self.mem_data), 'b-', linewidth=2, label='Memory')
        self.ax2.fill_between(times, list(self.mem_data), alpha=0.3, color='blue')
        self.ax2.set_title('Memory Usage (%)', fontweight='bold')
        self.ax2.set_ylim(0, 100)
        self.ax2.set_ylabel('Percentage')
        self.ax2.legend(loc='upper right')
        self.ax2.grid(True, alpha=0.3)

        # Plot Network Sent
        self.ax3.plot(times, list(self.net_sent_data), 'g-', linewidth=2, label='Sent', marker='o', markersize=2)
        self.ax3.set_title('Network Sent (MB)', fontweight='bold')
        self.ax3.set_ylabel('MB')
        self.ax3.legend(loc='upper right')
        self.ax3.grid(True, alpha=0.3)
        max_sent = max(self.net_sent_data) if self.net_sent_data else 1
        self.ax3.set_ylim(0, max(max_sent * 1.2, 0.1))

        # Plot Network Recv
        self.ax4.plot(times, list(self.net_recv_data), 'm-', linewidth=2, label='Received', marker='s', markersize=2)
        self.ax4.set_title('Network Received (MB)', fontweight='bold')
        self.ax4.set_ylabel('MB')
        self.ax4.legend(loc='upper right')
        self.ax4.grid(True, alpha=0.3)
        max_recv = max(self.net_recv_data) if self.net_recv_data else 1
        self.ax4.set_ylim(0, max(max_recv * 1.2, 0.1))

        # Plot Combined
        self.ax5.plot(times, list(self.cpu_data), 'r-', linewidth=2, label='CPU', alpha=0.7)
        self.ax5.plot(times, list(self.mem_data), 'b-', linewidth=2, label='Memory', alpha=0.7)
        self.ax5.set_title('Combined CPU & Memory Usage', fontweight='bold')
        self.ax5.set_ylim(0, 100)
        self.ax5.set_ylabel('Percentage')
        self.ax5.set_xlabel('Time (seconds)')
        self.ax5.legend(loc='upper right')
        self.ax5.grid(True, alpha=0.3)

        # Update main title
        elapsed = times[-1] if times else 0
        remaining = self.duration - elapsed
        self.fig.suptitle(
            f'Real-Time System Resource Monitoring (Time Remaining: {int(remaining)}s)\n'
            f'CPU: {current_data["cpu"]:.1f}% | Memory: {current_data["memory"]:.1f}% | '
            f'Net Sent: {current_data["network_sent"]:.2f}MB | Net Recv: {current_data["network_recv"]:.2f}MB',
            fontsize=14, fontweight='bold'
        )

        # Save graph
        os.makedirs('output', exist_ok=True)
        plt.tight_layout()
        self.fig.savefig('output/realtime_monitoring.png', dpi=100, bbox_inches='tight')

    def run(self):
        """Run the monitoring system"""
        print(f"Starting system monitoring for {self.duration} seconds...")
        print(f"Data collection interval: {self.interval} seconds")
        print(f"Graph updates saved to: output/realtime_monitoring.png")
        print("-" * 60)

        self.setup_realtime_plot()
        self.start_time = time.time()

        iteration = 0
        # Monitoring loop
        while True:
            elapsed = time.time() - self.start_time

            if elapsed >= self.duration:
                print(f"\n{'='*60}")
                print(f"Monitoring completed ({self.duration} seconds)")
                print(f"{'='*60}")
                break

            # Collect data
            current_data = self.collect_all_data()
            iteration += 1

            # Print progress
            print(f"[{iteration:3d}] Time: {elapsed:6.1f}s | "
                  f"CPU: {current_data['cpu']:5.1f}% | "
                  f"Mem: {current_data['memory']:5.1f}% | "
                  f"Net Sent: {current_data['network_sent']:7.2f}MB | "
                  f"Net Recv: {current_data['network_recv']:7.2f}MB")

            # Update graph every 10 iterations (or every 20 seconds)
            if iteration % 10 == 0:
                self.update_realtime_graph(current_data)
                print(f"  -> Graph updated (output/realtime_monitoring.png)")

            # Wait for next interval
            time.sleep(self.interval)

        # Final graph update
        self.update_realtime_graph(current_data)

        # Save data after monitoring
        self.save_data()

        print("\nMonitoring session completed!")
        print(f"Total data points collected: {len(self.data['timestamps'])}")
        return self.data

def main():
    monitor = SystemMonitor(duration=300, interval=2)  # 5 minutes, 2 second interval
    data = monitor.run()

    print("\nGenerating PDF report...")
    from generate_report import generate_pdf_report
    generate_pdf_report(data)

if __name__ == '__main__':
    main()
