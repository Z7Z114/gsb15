import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any
import os
from jinja2 import Template

from app.config import settings


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD

    def _create_connection(self):
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password]):
            return None
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            return server
        except Exception as e:
            print(f"Email connection error: {e}")
            return None

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "email")
        template_path = os.path.join(template_dir, f"{template_name}.html")

        if not os.path.exists(template_path):
            return self._render_default_template(template_name, context)

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        template = Template(template_content)
        return template.render(**context)

    def _render_default_template(self, template_name: str, context: Dict[str, Any]) -> str:
        title = context.get("title", "CSA会员通讯")
        content = context.get("content", "")
        recipes = context.get("recipes", [])

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 8px; }}
                .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; margin-top: 20px; }}
                .recipe {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #4CAF50; }}
                .recipe-title {{ color: #4CAF50; font-size: 18px; margin-bottom: 10px; }}
                .recipe-meta {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                h1, h2, h3 {{ color: #2E7D32; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🥬 CSA社区支持农业</h1>
                <p>{title}</p>
            </div>
            <div class="content">
                {content}
        """

        if recipes:
            html += "<h2>🍳 本周推荐食谱</h2>"
            for recipe in recipes:
                ingredients_html = "<ul>" + "".join([f"<li>{ing.get('name', '')}: {ing.get('quantity', '')}</li>" for ing in recipe.get('ingredients', [])]) + "</ul>"
                steps_html = "<ol>" + "".join([f"<li>{step}</li>" for step in recipe.get('steps', [])]) + "</ol>"
                html += f"""
                <div class="recipe">
                    <div class="recipe-title">🥗 {recipe.get('title', '')}</div>
                    <div class="recipe-meta">
                        用时: {recipe.get('cooking_time', 0)}分钟 | 难度: {recipe.get('difficulty', '')}
                    </div>
                    <div class="recipe-meta">
                        使用蔬菜: {', '.join(recipe.get('vegetables_used', []))}
                    </div>
                    <h4>食材:</h4>
                    {ingredients_html}
                    <h4>步骤:</h4>
                    {steps_html}
                </div>
                """

        html += """
            </div>
            <div class="footer">
                <p>感谢您加入CSA社区支持农业！</p>
                <p>如有任何问题，请回复此邮件联系我们。</p>
            </div>
        </body>
        </html>
        """
        return html

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        server = self._create_connection()
        if not server:
            print("Email service not configured")
            return False

        try:
            for to_email in to_emails:
                msg = MIMEMultipart("alternative")
                msg["From"] = self.smtp_user
                msg["To"] = to_email
                msg["Subject"] = subject

                html_part = MIMEText(html_content, "html", "utf-8")
                msg.attach(html_part)

                if attachments:
                    for att in attachments:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(att["content"])
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {att['filename']}"
                        )
                        msg.attach(part)

                server.sendmail(self.smtp_user, to_email, msg.as_string())

            server.quit()
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            if server:
                server.quit()
            return False

    async def send_newsletter(
        self,
        to_emails: List[str],
        title: str,
        content: str,
        recipes: List[Dict[str, Any]] = None
    ) -> bool:
        context = {
            "title": title,
            "content": content,
            "recipes": recipes or []
        }
        html_content = self.render_template("newsletter", context)
        return await self.send_email(to_emails, title, html_content)

    async def send_planting_intent_update(
        self,
        to_emails: List[str],
        planting_intent: Dict[str, Any]
    ) -> bool:
        vegetables_html = "<ul>" + "".join([
            f"<li>{v.get('name', '')} - 种植面积: {v.get('planting_area', 0)}亩, 预计产量: {v.get('expected_yield', 0)}公斤</li>"
            for v in planting_intent.get('next_season_vegetables', [])
        ]) + "</ul>"

        adjustments = planting_intent.get('share_adjustments', {})
        adjustments_html = "<ul>" + "".join([
            f"<li>{k}: {v}</li>" for k, v in adjustments.items()
        ]) + "</ul>"

        recommendations_html = "<ul>" + "".join([
            f"<li>{r}</li>" for r in planting_intent.get('recommendations', [])
        ]) + "</ul>"

        content = f"""
        <h2>🌱 下一季种植计划</h2>
        <p>亲爱的会员，以下是我们根据大家的反馈制定的下一季种植计划：</p>

        <h3>📋 拟种植蔬菜</h3>
        {vegetables_html}

        <h3>📊 份额调整</h3>
        {adjustments_html}

        <h3>💡 建议</h3>
        {recommendations_html}

        <p>如果您有任何意见或建议，请随时与我们联系！</p>
        """

        context = {
            "title": "下一季种植计划更新",
            "content": content,
            "recipes": []
        }

        html_content = self.render_template("newsletter", context)
        return await self.send_email(to_emails, "【CSA】下一季种植计划更新", html_content)

    async def send_meeting_summary(
        self,
        to_emails: List[str],
        meeting_summary: Dict[str, Any]
    ) -> bool:
        decisions_html = "<ul>" + "".join([
            f"<li>{d}</li>" for d in meeting_summary.get('key_decisions', [])
        ]) + "</ul>"

        actions_html = "<ul>" + "".join([
            f"<li>{a}</li>" for a in meeting_summary.get('action_items', [])
        ]) + "</ul>"

        next_steps_html = "<ul>" + "".join([
            f"<li>{n}</li>" for n in meeting_summary.get('next_steps', [])
        ]) + "</ul>"

        content = f"""
        <h2>📝 会员大会会议纪要</h2>
        <p>{meeting_summary.get('summary', '')}</p>

        <h3>🎯 重要决定</h3>
        {decisions_html}

        <h3>✅ 待办事项</h3>
        {actions_html}

        <h3>🚀 下一步计划</h3>
        {next_steps_html}
        """

        context = {
            "title": "会员大会会议纪要",
            "content": content,
            "recipes": []
        }

        html_content = self.render_template("newsletter", context)
        return await self.send_email(to_emails, "【CSA】会员大会会议纪要", html_content)

    async def send_weekly_update(
        self,
        to_emails: List[str],
        week_number: int,
        available_vegetables: List[Dict[str, Any]],
        recipes: List[Dict[str, Any]] = None,
        announcements: List[str] = None
    ) -> bool:
        vegetables_html = "<ul>" + "".join([
            f"<li><strong>{v.get('name', '')}</strong> - {v.get('description', '')}</li>"
            for v in available_vegetables
        ]) + "</ul>"

        announcements_html = ""
        if announcements:
            announcements_html = "<h3>📢 重要通知</h3><ul>" + "".join([
                f"<li>{a}</li>" for a in announcements
            ]) + "</ul>"

        content = f"""
        <h2>🌿 第{week_number}周菜篮子更新</h2>
        <p>亲爱的会员，本周我们为您准备了以下新鲜蔬菜：</p>

        <h3>🥬 本周蔬菜</h3>
        {vegetables_html}

        {announcements_html}

        <p>请记得按时领取您的菜篮子，如有任何问题请随时联系我们。</p>
        """

        context = {
            "title": f"第{week_number}周菜篮子更新",
            "content": content,
            "recipes": recipes or []
        }

        html_content = self.render_template("newsletter", context)
        return await self.send_email(to_emails, f"【CSA】第{week_number}周菜篮子更新", html_content)


email_service = EmailService()
