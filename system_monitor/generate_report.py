#!/usr/bin/env python3
"""
PDF Report Generator for System Resource Monitoring
Creates comprehensive PDF report with tables and graphs
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

def create_graphs(data):
    """Create all graphs and save as images"""
    os.makedirs('output/graphs', exist_ok=True)

    timestamps = data['timestamps']
    time_minutes = [t / 60 for t in timestamps]  # Convert to minutes

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')

    # 1. CPU Usage over Time
    plt.figure(figsize=(10, 4))
    plt.plot(time_minutes, data['cpu_percent'], 'r-', linewidth=2, label='CPU Usage')
    plt.fill_between(time_minutes, data['cpu_percent'], alpha=0.3, color='red')
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('CPU Usage (%)', fontsize=12)
    plt.title('CPU Usage Over Time', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig('output/graphs/cpu_usage.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Memory Usage over Time
    plt.figure(figsize=(10, 4))
    plt.plot(time_minutes, data['memory_percent'], 'b-', linewidth=2, label='Memory Usage')
    plt.fill_between(time_minutes, data['memory_percent'], alpha=0.3, color='blue')
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Memory Usage (%)', fontsize=12)
    plt.title('Memory Usage Over Time', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig('output/graphs/memory_usage.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 3. CPU and Memory Combined
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

    ax1.plot(time_minutes, data['cpu_percent'], 'r-', linewidth=2, label='CPU')
    ax1.fill_between(time_minutes, data['cpu_percent'], alpha=0.3, color='red')
    ax1.set_ylabel('CPU Usage (%)', fontsize=11)
    ax1.set_title('CPU & Memory Usage Comparison', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 100)

    ax2.plot(time_minutes, data['memory_percent'], 'b-', linewidth=2, label='Memory')
    ax2.fill_between(time_minutes, data['memory_percent'], alpha=0.3, color='blue')
    ax2.set_xlabel('Time (minutes)', fontsize=11)
    ax2.set_ylabel('Memory Usage (%)', fontsize=11)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig('output/graphs/cpu_memory_combined.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 4. Network Traffic
    plt.figure(figsize=(10, 4))
    plt.plot(time_minutes, data['network_sent'], 'g-', linewidth=2, label='Sent', marker='o', markersize=3)
    plt.plot(time_minutes, data['network_recv'], 'm-', linewidth=2, label='Received', marker='s', markersize=3)
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Data Transfer (MB)', fontsize=12)
    plt.title('Network Traffic Over Time', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('output/graphs/network_traffic.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 5. Disk I/O
    plt.figure(figsize=(10, 4))
    plt.plot(time_minutes, data['disk_read'], 'c-', linewidth=2, label='Read', marker='^', markersize=3)
    plt.plot(time_minutes, data['disk_write'], 'orange', linewidth=2, label='Write', marker='v', markersize=3)
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Data Transfer (MB)', fontsize=12)
    plt.title('Disk I/O Over Time', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('output/graphs/disk_io.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 6. CPU per Core (if available and multiple cores)
    if data['cpu_per_core'] and len(data['cpu_per_core'][0]) > 1:
        plt.figure(figsize=(10, 5))
        cpu_cores = np.array(data['cpu_per_core'])
        for i in range(cpu_cores.shape[1]):
            plt.plot(time_minutes, cpu_cores[:, i], linewidth=1.5, label=f'Core {i}', alpha=0.7)

        plt.xlabel('Time (minutes)', fontsize=12)
        plt.ylabel('CPU Usage (%)', fontsize=12)
        plt.title('CPU Usage Per Core', fontsize=14, fontweight='bold')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 100)
        plt.tight_layout()
        plt.savefig('output/graphs/cpu_per_core.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 7. Statistical Summary (Box Plot)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    box_data = [data['cpu_percent'], data['memory_percent']]
    bp1 = axes[0].boxplot(box_data, labels=['CPU', 'Memory'], patch_artist=True)
    axes[0].set_ylabel('Usage (%)', fontsize=11)
    axes[0].set_title('CPU & Memory Usage Distribution', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3, axis='y')

    # Color boxes
    colors_box = ['lightcoral', 'lightblue']
    for patch, color in zip(bp1['boxes'], colors_box):
        patch.set_facecolor(color)

    # Disk usage pie chart
    disk_total = data['disk_usage'][-1] if data['disk_usage'] else 0
    disk_free = 100 - disk_total
    axes[1].pie(
        [disk_total, disk_free],
        labels=['Used', 'Free'],
        autopct='%1.1f%%',
        colors=['lightcoral', 'lightgreen'],
        startangle=90
    )
    axes[1].set_title('Disk Usage', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig('output/graphs/statistics.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("All graphs created successfully!")

def calculate_statistics(data):
    """Calculate statistics from monitoring data"""
    stats = {}

    # CPU stats
    stats['cpu'] = {
        'mean': np.mean(data['cpu_percent']),
        'median': np.median(data['cpu_percent']),
        'min': np.min(data['cpu_percent']),
        'max': np.max(data['cpu_percent']),
        'std': np.std(data['cpu_percent'])
    }

    # Memory stats
    stats['memory'] = {
        'mean': np.mean(data['memory_percent']),
        'median': np.median(data['memory_percent']),
        'min': np.min(data['memory_percent']),
        'max': np.max(data['memory_percent']),
        'std': np.std(data['memory_percent']),
        'avg_used_gb': np.mean(data['memory_used']),
        'avg_available_gb': np.mean(data['memory_available'])
    }

    # Network stats
    total_sent = data['network_sent'][-1] if data['network_sent'] else 0
    total_recv = data['network_recv'][-1] if data['network_recv'] else 0

    stats['network'] = {
        'total_sent_mb': total_sent,
        'total_recv_mb': total_recv,
        'avg_sent_rate': total_sent / (data['timestamps'][-1] / 60) if data['timestamps'] else 0,
        'avg_recv_rate': total_recv / (data['timestamps'][-1] / 60) if data['timestamps'] else 0
    }

    # Disk stats
    total_read = data['disk_read'][-1] if data['disk_read'] else 0
    total_write = data['disk_write'][-1] if data['disk_write'] else 0

    stats['disk'] = {
        'total_read_mb': total_read,
        'total_write_mb': total_write,
        'avg_usage': np.mean(data['disk_usage']) if data['disk_usage'] else 0
    }

    return stats

def generate_pdf_report(data):
    """Generate comprehensive PDF report"""
    output_file = 'output/system_monitoring_report.pdf'
    os.makedirs('output', exist_ok=True)

    # Create graphs first
    create_graphs(data)

    # Calculate statistics
    stats = calculate_statistics(data)

    # Create PDF
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40
    )

    # Container for elements
    story = []

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    normal_style = styles['Normal']

    # Title
    title = Paragraph("System Resource Monitoring Report", title_style)
    story.append(title)

    # Subtitle with timestamp
    subtitle = Paragraph(
        f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
        f"<b>Monitoring Duration:</b> {data['timestamps'][-1] / 60:.1f} minutes<br/>"
        f"<b>Data Points Collected:</b> {len(data['timestamps'])}",
        normal_style
    )
    story.append(subtitle)
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))

    summary_data = [
        ['Metric', 'Average', 'Min', 'Max', 'Std Dev'],
        [
            'CPU Usage (%)',
            f"{stats['cpu']['mean']:.2f}",
            f"{stats['cpu']['min']:.2f}",
            f"{stats['cpu']['max']:.2f}",
            f"{stats['cpu']['std']:.2f}"
        ],
        [
            'Memory Usage (%)',
            f"{stats['memory']['mean']:.2f}",
            f"{stats['memory']['min']:.2f}",
            f"{stats['memory']['max']:.2f}",
            f"{stats['memory']['std']:.2f}"
        ],
        [
            'Disk Usage (%)',
            f"{stats['disk']['avg_usage']:.2f}",
            '-',
            '-',
            '-'
        ]
    ]

    summary_table = Table(summary_data, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Network Summary Table
    story.append(Paragraph("Network & Disk I/O Summary", heading_style))

    network_data = [
        ['Resource', 'Metric', 'Value'],
        ['Network', 'Total Data Sent', f"{stats['network']['total_sent_mb']:.2f} MB"],
        ['Network', 'Total Data Received', f"{stats['network']['total_recv_mb']:.2f} MB"],
        ['Network', 'Avg Send Rate', f"{stats['network']['avg_sent_rate']:.2f} MB/min"],
        ['Network', 'Avg Receive Rate', f"{stats['network']['avg_recv_rate']:.2f} MB/min"],
        ['Disk I/O', 'Total Read', f"{stats['disk']['total_read_mb']:.2f} MB"],
        ['Disk I/O', 'Total Write', f"{stats['disk']['total_write_mb']:.2f} MB"],
    ]

    network_table = Table(network_data, colWidths=[2*inch, 2.5*inch, 2.5*inch])
    network_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))

    story.append(network_table)
    story.append(Spacer(1, 20))

    # Temperature Info (if available)
    if data['temperatures'] and data['temperatures'][0]:
        temps = data['temperatures'][0]
        if 'note' not in temps:
            story.append(Paragraph("Temperature Sensors", heading_style))
            temp_data = [['Sensor', 'Temperature (°C)']]
            for sensor, temp in temps.items():
                temp_data.append([sensor, f"{temp:.1f}"])

            temp_table = Table(temp_data, colWidths=[4*inch, 3*inch])
            temp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            story.append(temp_table)
            story.append(Spacer(1, 20))

    # Page break before graphs
    story.append(PageBreak())

    # Graphs Section
    story.append(Paragraph("Detailed Analysis - Graphs", heading_style))
    story.append(Spacer(1, 10))

    # Add graphs
    graph_files = [
        ('output/graphs/cpu_usage.png', 'CPU Usage Over Time'),
        ('output/graphs/memory_usage.png', 'Memory Usage Over Time'),
        ('output/graphs/cpu_memory_combined.png', 'CPU & Memory Comparison'),
        ('output/graphs/network_traffic.png', 'Network Traffic'),
        ('output/graphs/disk_io.png', 'Disk I/O'),
        ('output/graphs/statistics.png', 'Statistical Summary')
    ]

    # Add CPU per core if exists
    if os.path.exists('output/graphs/cpu_per_core.png'):
        graph_files.append(('output/graphs/cpu_per_core.png', 'CPU Usage Per Core'))

    for graph_file, caption in graph_files:
        if os.path.exists(graph_file):
            story.append(Paragraph(f"<b>{caption}</b>", normal_style))
            story.append(Spacer(1, 5))

            img = Image(graph_file, width=6.5*inch, height=3*inch)
            story.append(img)
            story.append(Spacer(1, 15))

            # Page break after every 2 graphs
            if graph_files.index((graph_file, caption)) % 2 == 1:
                story.append(PageBreak())

    # Build PDF
    doc.build(story)

    print(f"\nPDF report generated successfully: {output_file}")
    print(f"Report includes:")
    print(f"  - Executive summary with statistics")
    print(f"  - Network and disk I/O summary")
    print(f"  - {len(graph_files)} detailed graphs")
    print(f"  - {len(data['timestamps'])} data points analyzed")

    return output_file

def main():
    """Load data and generate report"""
    data_file = 'data/monitoring_data.json'

    if not os.path.exists(data_file):
        print(f"Error: Data file '{data_file}' not found!")
        print("Please run monitor.py first to collect data.")
        return

    with open(data_file, 'r') as f:
        data = json.load(f)

    generate_pdf_report(data)

if __name__ == '__main__':
    main()
