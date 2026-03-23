# 期刊追踪系统 - 云端接收端
# Flask API 接收本地发送的论文数据

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import logging

# ============================================================
# 配置
# ============================================================

app = Flask(__name__)
CORS(app)

# API 密钥（用于验证请求）
API_KEY = os.environ.get("JOURNAL_API_KEY", "your-secret-api-key")

# 163 邮箱配置
EMAIL_SMTP_SERVER = "smtp.163.com"
EMAIL_SMTP_PORT = 465
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "your-163-email@163.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "your-smtp-password")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "your-receiver-email@163.com")

# 数据存储目录
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# 邮件推送
# ============================================================

def send_daily_email(papers):
    """发送每日推送邮件"""
    if not papers:
        logger.info("没有新论文，跳过邮件发送")
        return True
    
    try:
        subject = f"【期刊日报】{datetime.now().strftime('%Y-%m-%d')} - {len(papers)} 篇新论文"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; }}
                .paper {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }}
                .journal {{ color: #e74c3c; font-weight: bold; }}
                .title {{ font-size: 16px; margin: 10px 0; }}
                .innovation {{ background: #f8f9fa; padding: 10px; border-left: 3px solid #3498db; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📚 期刊文献日报</h2>
                <p>{datetime.now().strftime('%Y年%m月%d日 %A')}</p>
                <p>今日新论文：<strong>{len(papers)} 篇</strong></p>
            </div>
        """
        
        for i, paper in enumerate(papers, 1):
            html_content += f"""
            <div class="paper">
                <div class="journal">{paper.get('journal', 'Unknown Journal')}</div>
                <div class="title">{i}. {paper.get('title', 'No Title')}</div>
                <div class="innovation">
                    <strong>🔬 创新点：</strong><br>
                    {paper.get('innovation_summary', '待分析...')}
                </div>
                <div style="margin-top: 10px;">
                    <a href="{paper.get('url', '#')}" target="_blank">📄 查看全文</a>
                </div>
            </div>
            """
        
        html_content += """
            <div class="footer">
                <p>此邮件由四川大学期刊自动追踪系统自动生成</p>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        server = smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        
        logger.info(f"日报邮件发送成功：{len(papers)} 篇论文")
        return True
        
    except Exception as e:
        logger.error(f"邮件发送失败：{e}")
        return False


def send_weekly_email(papers):
    """发送每周汇总邮件"""
    if not papers:
        return True
    
    try:
        journal_stats = {}
        for paper in papers:
            journal = paper.get('journal', 'Unknown')
            journal_stats[journal] = journal_stats.get(journal, 0) + 1
        
        week_start = datetime.now() - timedelta(days=7)
        subject = f"【期刊周报】{week_start.strftime('%m.%d')}-{datetime.now().strftime('%m.%d')} - {len(papers)} 篇"
        
        html_content = f"""
        <html><head><style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background: #34495e; color: white; padding: 20px; }}
            .stats {{ background: #ecf0f1; padding: 15px; margin: 20px 0; }}
        </style></head><body>
        <div class="header"><h2>📊 期刊周报</h2>
        <p>{week_start.strftime('%Y年%m月%d日')} - {datetime.now().strftime('%Y年%m月%d日')}</p>
        <p>本周新论文：<strong>{len(papers)} 篇</strong></p></div>
        <div class="stats"><h3>📈 期刊分布</h3><ul>
        """
        
        for journal, count in sorted(journal_stats.items(), key=lambda x: x[1], reverse=True):
            html_content += f"<li>{journal}: {count} 篇</li>"
        
        html_content += "</ul></div><div class='stats'><h3>📋 论文列表</h3><ul>"
        
        for paper in papers:
            html_content += f"<li><strong>{paper.get('journal', 'Unknown')}</strong>: {paper.get('title', 'No Title')} <a href='{paper.get('url', '#')}'>[链接]</a></li>"
        
        html_content += "</ul></div></body></html>"
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        server = smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        
        logger.info(f"周报邮件发送成功")
        return True
        
    except Exception as e:
        logger.error(f"周报邮件发送失败：{e}")
        return False
    
    # ============================================================
# AI 分析（简化版）
# ============================================================

def analyze_paper(paper):
    """分析单篇论文，提取创新点"""
    title = paper.get('title', '')
    journal = paper.get('journal', '')
    innovation = f"[AI 分析中...] 该研究发表于 {journal}，标题为《{title}》。详细创新点分析将在完整版中提供。"
    
    return {
        **paper,
        "innovation_summary": innovation,
        "analyzed_at": datetime.now().isoformat()
    }


# ============================================================
# API 端点
# ============================================================

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "journal-tracker-receiver"
    })


@app.route('/receive', methods=['POST'])
def receive_papers():
    """接收本地发送的论文数据"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing authorization"}), 401
        
        token = auth_header.replace('Bearer ', '')
        if token != API_KEY:
            return jsonify({"error": "Invalid API key"}), 403
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        mode = data.get('mode', 'daily')
        papers = data.get('papers', [])
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        logger.info(f"接收到 {len(papers)} 篇论文 (模式：{mode})")
        
        if not papers:
            return jsonify({"status": "success", "message": "No papers"})
        
        # 保存原始数据
        data_file = DATA_DIR / f"papers_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # AI 分析
        analyzed_papers = [analyze_paper(p) for p in papers]
        
        # 保存分析数据
        analyzed_file = DATA_DIR / f"analyzed_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analyzed_file, 'w', encoding='utf-8') as f:
            json.dump({"papers": analyzed_papers, "timestamp": timestamp}, f, ensure_ascii=False, indent=2)
        
        # 发送邮件
        email_success = send_daily_email(analyzed_papers) if mode == 'daily' else send_weekly_email(analyzed_papers)
        
        return jsonify({
            "status": "success",
            "message": f"Processed {len(papers)} papers",
            "mode": mode,
            "email_sent": email_success
        })
        
    except Exception as e:
        logger.error(f"处理数据失败：{e}")
        return jsonify({"error": str(e)}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    try:
        data_files = list(DATA_DIR.glob("papers_*.json"))
        total_papers = sum(len(json.load(open(f))) for f in data_files)
        
        return jsonify({
            "total_runs": len(data_files),
            "total_papers": total_papers
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 主程序
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"启动期刊追踪接收端，端口：{port}")
    app.run(host='0.0.0.0', port=port, debug=False)