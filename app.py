"""
=============================================================
ILANIA DIGITAL MARKETPLACE — Single-File Flask App (app.py)
Creator: Raj Gautam (GitHub: @Rg100152)
=============================================================
Run:
    pip install flask flask-sqlalchemy flask-login
    python3 app.py

Visit: http://127.0.0.1:5000
=============================================================
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os, uuid, random

# ============================================================
# 1. CONFIGURATION
# ============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ilania-marketplace-secret-key-raj-gautam-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB Max Upload

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ============================================================
# 2. DATABASE MODELS (8 Tables as per ER Diagram)
# ============================================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='buyer')  # buyer / seller / admin
    phone = db.Column(db.String(20), default='')
    avatar = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True)
    icon = db.Column(db.String(20), default='📦')
    description = db.Column(db.Text, default='')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True)
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, default=0.0)
    image = db.Column(db.String(300), default='')
    file = db.Column(db.String(200), default='')
    status = db.Column(db.String(20), default='pending')  # pending / approved / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    seller = db.relationship('User', backref='products')
    category = db.relationship('Category', backref='products')

    def avg_rating(self):
        reviews = Review.query.filter_by(product_id=self.id).all()
        if not reviews:
            return 4.9
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='paid')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')

class Download(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True)
    downloaded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ============================================================
# 3. MASTER CSS & ANIMATIONS (Dark Theme + 20+ Effects)
# ============================================================
BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { margin:0; padding:0; box-sizing:border-box; }
:root {
    --bg-dark: #0f0f1e;
    --bg-card: #16213e;
    --bg-hover: #1e2a4a;
    --accent: #ff6b35;
    --accent-hover: #ff8456;
    --text: #e8e8f0;
    --text-dim: #a0a0b8;
    --border: #2a2a3e;
    --success: #2ecc71;
    --danger: #e74c3c;
    --radius: 14px;
    --t: 0.3s cubic-bezier(0.2, 0.9, 0.3, 1);
}

body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--bg-dark);
    color: var(--text);
    line-height: 1.6;
    overflow-x: hidden;
}
a { color: inherit; text-decoration: none; }
img { max-width: 100%; display: block; }
ul { list-style: none; }

/* MARQUEE TOP BAR */
.marquee {
    background: linear-gradient(90deg, #ff6b35, #ff8456, #9b59ff);
    color: #fff; overflow: hidden; padding: 6px 0;
    font-size: 0.78rem; font-weight: 600;
    position: fixed; top: 0; left: 0; right: 0; z-index: 1001;
}
.marquee-track {
    display: flex; gap: 50px; white-space: nowrap;
    animation: marquee 25s linear infinite; width: max-content;
}
@keyframes marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }

/* SCROLL PROGRESS */
.scroll-progress {
    position: fixed; top: 30px; left: 0; height: 3px;
    background: linear-gradient(90deg, var(--accent), #ffb347);
    z-index: 1002; width: 0%; transition: width 0.1s linear;
    box-shadow: 0 0 10px var(--accent);
}

/* NAVBAR */
.navbar {
    position: fixed; top: 30px; left: 0; right: 0; z-index: 1000;
    padding: 16px 0; background: rgba(15, 15, 30, 0.6);
    backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: all var(--t);
}
.navbar.scrolled {
    padding: 10px 0; background: rgba(15, 15, 30, 0.92);
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}
.nav-container {
    max-width: 1360px; margin: 0 auto; padding: 0 24px;
    display: flex; align-items: center; justify-content: space-between; gap: 20px;
}
.nav-logo { font-size: 1.45rem; font-weight: 800; display: flex; align-items: center; gap: 10px; }
.logo-icon {
    display: inline-flex; width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--accent), #ffb347);
    color: #fff; border-radius: 9px; align-items: center; justify-content: center;
    font-size: 0.9rem; box-shadow: 0 4px 15px rgba(255,107,53,0.4);
}
.nav-search { flex: 1; max-width: 440px; position: relative; }
.nav-search input {
    width: 100%; padding: 10px 40px 10px 16px;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; color: var(--text); outline: none; font-size: 0.88rem;
    transition: all var(--t);
}
.nav-search input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(255,107,53,0.15); }
.search-btn { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1rem; }

.nav-links { display: flex; gap: 22px; font-size: 0.9rem; font-weight: 500; }
.nav-links a { transition: color var(--t); }
.nav-links a:hover { color: var(--accent); }

.nav-actions { display: flex; align-items: center; gap: 10px; }
.cart-icon {
    position: relative; font-size: 1.25rem; padding: 8px 12px;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; transition: all var(--t);
}
.cart-icon:hover { border-color: var(--accent); }
.cart-badge {
    position: absolute; top: -5px; right: -5px;
    background: var(--accent); color: #fff; font-size: 0.68rem;
    font-weight: 800; padding: 2px 6px; border-radius: 10px;
}

/* BUTTONS */
.btn-primary, .btn-outline {
    padding: 9px 18px; border-radius: 10px; font-size: 0.85rem;
    font-weight: 600; cursor: pointer; border: none;
    transition: all var(--t); display: inline-flex; align-items: center; gap: 6px;
    position: relative; overflow: hidden;
}
.btn-primary { background: linear-gradient(135deg, var(--accent), #ff8456); color: #fff; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(255,107,53,0.45); }
.btn-outline { background: rgba(255,255,255,0.03); color: var(--text); border: 1px solid var(--border); }
.btn-outline:hover { border-color: var(--accent); color: var(--accent); background: rgba(255,107,53,0.08); }
.btn-lg { padding: 13px 26px; font-size: 0.98rem; }

/* LAYOUT */
main { padding-top: 100px; min-height: 75vh; animation: pageIn 0.45s ease; }
@keyframes pageIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.container { max-width: 1360px; margin: 0 auto; padding: 0 24px; }
.section { padding: 65px 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 36px; flex-wrap: wrap; gap: 15px; }
.section-header h2 { font-size: 1.9rem; font-weight: 800; }
.view-all { color: var(--accent); font-weight: 600; font-size: 0.92rem; }

/* HERO + AURORA + PARTICLES */
.hero {
    min-height: 82vh; display: flex; align-items: center; text-align: center;
    position: relative; overflow: hidden; padding: 40px 0;
}
.aurora { position: absolute; inset: 0; overflow: hidden; z-index: 0; pointer-events: none; }
.aurora::before, .aurora::after {
    content: ''; position: absolute; width: 55%; height: 55%;
    border-radius: 50%; filter: blur(90px); opacity: 0.32;
}
.aurora::before {
    background: radial-gradient(circle, #ff6b35, transparent 70%);
    top: -15%; left: -10%; animation: auroraMove 10s ease-in-out infinite alternate;
}
.aurora::after {
    background: radial-gradient(circle, #9b59ff, transparent 70%);
    bottom: -15%; right: -10%; animation: auroraMove 13s ease-in-out infinite alternate-reverse;
}
@keyframes auroraMove { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(20%,15%) scale(1.25); } }

.ripple-grid {
    position: absolute; inset: 0; pointer-events: none;
    background-image: linear-gradient(rgba(255,107,53,0.05) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255,107,53,0.05) 1px, transparent 1px);
    background-size: 42px 42px;
    mask-image: radial-gradient(circle at 50% 50%, #000 10%, transparent 75%);
}
#particleCanvas { position: absolute; inset: 0; z-index: 0; pointer-events: none; width: 100%; height: 100%; }

.hero-content { position: relative; z-index: 2; width: 100%; }
@keyframes heroFadeUp { from { opacity:0; transform:translateY(35px); } to { opacity:1; transform:translateY(0); } }
.hero-title {
    font-size: clamp(2.2rem, 5vw, 4.1rem); font-weight: 800; line-height: 1.12;
    margin-bottom: 18px; animation: heroFadeUp 0.8s ease 0.1s both;
}
.accent { color: var(--accent); }
.hero-subtitle {
    font-size: 1.1rem; color: var(--text-dim); max-width: 620px;
    margin: 0 auto 30px; animation: heroFadeUp 0.8s ease 0.25s both;
}
.hero-cta { display: flex; justify-content: center; gap: 14px; flex-wrap: wrap; animation: heroFadeUp 0.8s ease 0.4s both; }
.hero-stats {
    display: flex; justify-content: center; gap: 48px; margin-top: 55px;
    flex-wrap: wrap; animation: heroFadeUp 0.8s ease 0.55s both;
}
.hero-stats div {
    background: rgba(22, 33, 62, 0.7); border: 1px solid var(--border);
    padding: 16px 28px; border-radius: 14px; backdrop-filter: blur(8px);
}
.hero-stats strong { font-size: 1.8rem; color: var(--accent); display: block; }
.hero-stats span { color: var(--text-dim); font-size: 0.82rem; }

/* PRODUCT CARDS + SPOTLIGHT + 3D TILT */
.product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(275px, 1fr)); gap: 24px; }
.product-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius); overflow: hidden;
    transition: all var(--t); position: relative;
    display: flex; flex-direction: column;
}
.product-card::before {
    content: ''; position: absolute; width: 350px; height: 350px;
    left: var(--mx, 50%); top: var(--my, 50%);
    background: radial-gradient(circle, rgba(255,107,53,0.16), transparent 70%);
    transform: translate(-50%, -50%); pointer-events: none;
    opacity: 0; transition: opacity 0.3s ease; z-index: 1;
}
.product-card:hover::before { opacity: 1; }
.product-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 45px rgba(255,107,53,0.22);
    border-color: var(--accent);
}
.img-wrap { position: relative; overflow: hidden; aspect-ratio: 16/10; background: #1a1a2e; }
.img-wrap img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease; }
.product-card:hover .img-wrap img { transform: scale(1.08); }
.product-info { padding: 18px; position: relative; z-index: 2; flex: 1; display: flex; flex-direction: column; }
.badge {
    display: inline-block; background: rgba(255,107,53,0.15); color: var(--accent);
    font-size: 0.72rem; font-weight: 700; padding: 4px 10px;
    border-radius: 20px; margin-bottom: 8px; width: fit-content;
}
.product-info h3 { font-size: 1.05rem; font-weight: 700; margin-bottom: 4px; }
.seller { color: var(--text-dim); font-size: 0.82rem; margin-bottom: 14px; }
.card-footer {
    margin-top: auto; display: flex; justify-content: space-between;
    align-items: center; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06);
}
.price { color: var(--accent); font-weight: 800; font-size: 1.2rem; }
.rating { color: #ffc107; font-size: 0.85rem; font-weight: 600; }

/* 3D FLIP CATEGORY CARDS */
.category-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 20px; }
.flip-card { perspective: 1000px; height: 165px; display: block; }
.flip-inner {
    position: relative; width: 100%; height: 100%;
    transition: transform 0.65s cubic-bezier(0.7, 0, 0.3, 1);
    transform-style: preserve-3d;
}
.flip-card:hover .flip-inner { transform: rotateY(180deg); }
.flip-face {
    position: absolute; inset: 0; backface-visibility: hidden;
    border-radius: var(--radius); display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: var(--bg-card); border: 1px solid var(--border); padding: 20px;
}
.flip-back {
    transform: rotateY(180deg);
    background: linear-gradient(135deg, var(--accent), #ff8456);
    color: #fff; text-align: center; border-color: var(--accent);
}

/* FORMS & TABLES */
.form-box {
    max-width: 460px; margin: 50px auto; background: var(--bg-card);
    border: 1px solid var(--border); border-radius: var(--radius); padding: 36px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
}
.form-box h2 { margin-bottom: 22px; text-align: center; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 6px; font-size: 0.85rem; color: var(--text-dim); font-weight: 500; }
.form-group input, .form-group select, .form-group textarea {
    width: 100%; padding: 11px 14px; background: var(--bg-dark);
    border: 1px solid var(--border); border-radius: 10px;
    color: var(--text); outline: none; font-family: inherit; font-size: 0.92rem;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: var(--accent); }
.table { width: 100%; background: var(--bg-card); border-radius: var(--radius); overflow: hidden; border-collapse: collapse; border: 1px solid var(--border); }
.table th, .table td { padding: 14px 18px; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
.table th { background: var(--bg-hover); font-weight: 700; color: #fff; }
.table tr:hover { background: rgba(255,255,255,0.02); }

/* TOASTS & ALERTS */
.alert {
    padding: 14px 20px; border-radius: 10px; margin-bottom: 16px;
    background: rgba(255,107,53,0.15); border-left: 4px solid var(--accent);
    font-weight: 500; animation: slideInRight 0.35s ease;
}
.alert.success { background: rgba(46,204,113,0.15); border-left-color: var(--success); }
.alert.error { background: rgba(231,76,60,0.15); border-left-color: var(--danger); }
@keyframes slideInRight { from { transform: translateX(60px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

/* SCROLL REVEAL */
.reveal { opacity: 0; transform: translateY(30px); transition: all 0.65s ease; }
.reveal.visible { opacity: 1; transform: translateY(0); }

/* RIPPLE & CURSOR DOT */
.ripple {
    position: absolute; border-radius: 50%; background: rgba(255,255,255,0.5);
    transform: scale(0); animation: rippleAnim 0.6s linear; pointer-events: none;
}
@keyframes rippleAnim { to { transform: scale(4); opacity: 0; } }
.cursor-dot {
    position: fixed; pointer-events: none; width: 6px; height: 6px;
    background: var(--accent); border-radius: 50%; z-index: 9998;
    transform: translate(-50%, -50%); animation: dotFade 0.7s ease forwards;
}
@keyframes dotFade { from { opacity:1; transform:translate(-50%,-50%) scale(1); } to { opacity:0; transform:translate(-50%,-50%) scale(0); } }

/* FOOTER */
.footer { background: var(--bg-card); border-top: 1px solid var(--border); margin-top: 80px; padding: 60px 0 24px; }
.footer-container { max-width: 1360px; margin: 0 auto; padding: 0 24px; display: grid; grid-template-columns: 2fr 1fr 1fr 1.5fr; gap: 40px; }
.footer-col h3, .footer-col h4 { margin-bottom: 16px; }
.footer-col p, .footer-col a { display: block; color: var(--text-dim); font-size: 0.88rem; margin-bottom: 10px; transition: color var(--t); }
.footer-col a:hover { color: var(--accent); }
.footer-bottom { text-align: center; padding-top: 24px; margin-top: 40px; border-top: 1px solid var(--border); color: var(--text-dim); font-size: 0.82rem; }

@media (max-width: 968px) {
    .nav-search, .nav-links { display: none; }
    .footer-container { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 600px) {
    .footer-container { grid-template-columns: 1fr; }
}
"""

# ============================================================
# 4. MASTER BASE TEMPLATE (Jinja2 Inline)
# ============================================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Ilania — Digital Marketplace{% endblock %}</title>
    <style>""" + BASE_CSS + """</style>
</head>
<body>

<!-- TOP MARQUEE -->
<div class="marquee">
    <div class="marquee-track">
        <span>🔥 Welcome to Ilania Digital Marketplace — Built by Raj Gautam</span>
        <span>⚡ Use Promo Code <b>SAVE10</b> for 10% Instant Discount at Checkout!</span>
        <span>🚀 Instant Token-Verified Digital Downloads</span>
        <span>🔥 Welcome to Ilania Digital Marketplace — Built by Raj Gautam</span>
        <span>⚡ Use Promo Code <b>SAVE10</b> for 10% Instant Discount at Checkout!</span>
    </div>
</div>

<!-- SCROLL PROGRESS -->
<div class="scroll-progress" id="scrollProgress"></div>

<!-- NAVBAR -->
<nav class="navbar" id="navbar">
    <div class="nav-container">
        <a href="{{ url_for('home') }}" class="nav-logo">
            <span class="logo-icon">▶</span> <span class="logo-text">Ilania</span>
        </a>
        <div class="nav-search">
            <form action="{{ url_for('search') }}" method="get">
                <input type="text" name="q" placeholder="Search UI kits, templates, graphics..." value="{{ request.args.get('q', '') }}">
                <button type="submit" class="search-btn">🔍</button>
            </form>
        </div>
        <ul class="nav-links">
            <li><a href="{{ url_for('home') }}">Home</a></li>
            <li><a href="{{ url_for('products') }}">Explore</a></li>
            <li><a href="{{ url_for('about') }}">About Creator</a></li>
        </ul>
        <div class="nav-actions">
            <a href="{{ url_for('cart') }}" class="cart-icon" id="cartIcon">
                🛒 <span class="cart-badge" id="cartBadge">{{ cart_count|default(0) }}</span>
            </a>
            {% if current_user.is_authenticated %}
                <a href="{{ url_for('profile') }}" class="btn-outline">👤 {{ current_user.username }} ({{ current_user.role|upper }})</a>
                {% if current_user.role == 'seller' %}
                    <a href="{{ url_for('seller_dashboard') }}" class="btn-outline">🏪 Studio</a>
                {% endif %}
                {% if current_user.role == 'admin' %}
                    <a href="{{ url_for('admin_dashboard') }}" class="btn-outline">🛡️ Admin</a>
                {% endif %}
                <a href="{{ url_for('logout') }}" class="btn-primary">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}" class="btn-outline">Login</a>
                <a href="{{ url_for('register') }}" class="btn-primary">Sign Up</a>
            {% endif %}
        </div>
    </div>
</nav>

<!-- MAIN CONTENT -->
<main>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="container" style="padding-top: 15px;">
                {% for cat, msg in messages %}
                    <div class="alert {{ cat }}">{{ msg }}</div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
</main>

<!-- FOOTER -->
<footer class="footer">
    <div class="footer-container">
        <div class="footer-col">
            <h3><span class="logo-icon">▶</span> Ilania Marketplace</h3>
            <p>Premium dark-theme digital marketplace for developers & creators. Built with Python & Flask by <strong>Raj Gautam</strong>.</p>
        </div>
        <div class="footer-col">
            <h4>Marketplace</h4>
            <a href="{{ url_for('products') }}">All Digital Assets</a>
            <a href="{{ url_for('products') }}?cat=1">Templates</a>
            <a href="{{ url_for('products') }}?cat=2">UI Kits</a>
            <a href="{{ url_for('cart') }}">Shopping Cart</a>
        </div>
        <div class="footer-col">
            <h4>Quick Links</h4>
            <a href="{{ url_for('about') }}">About Raj Gautam</a>
            <a href="{{ url_for('login') }}">Demo Accounts Login</a>
            <a href="https://github.com/Rg100152" target="_blank">GitHub (@Rg100152)</a>
        </div>
        <div class="footer-col">
            <h4>Quick Demo Switch</h4>
            <p>Test roles with 1-click login:</p>
            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;">
                <a href="{{ url_for('quick_login', role='buyer') }}" class="btn-outline" style="padding:5px 10px; font-size:0.75rem;">👤 Buyer</a>
                <a href="{{ url_for('quick_login', role='seller') }}" class="btn-outline" style="padding:5px 10px; font-size:0.75rem;">🏪 Seller</a>
                <a href="{{ url_for('quick_login', role='admin') }}" class="btn-outline" style="padding:5px 10px; font-size:0.75rem;">🛡️ Admin</a>
            </div>
        </div>
    </div>
    <div class="footer-bottom">© 2026 Ilania Digital Marketplace · Crafted by Raj Gautam</div>
</footer>

<!-- MASTER JAVASCRIPT (20+ Animations) -->
<script>
// 1. Navbar Shrink + Scroll Progress Bar
window.addEventListener('scroll', () => {
    document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 40);
    const h = document.documentElement.scrollHeight - window.innerHeight;
    document.getElementById('scrollProgress').style.width = (h > 0 ? (window.scrollY / h * 100) : 0) + '%';
});

// 2. Scroll Reveal Observer
const revealObs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            e.target.classList.add('visible');
            revealObs.unobserve(e.target);
        }
    });
}, { threshold: 0.1 });
document.querySelectorAll('.section, .product-card, .flip-card, .reveal').forEach(el => {
    el.classList.add('reveal');
    revealObs.observe(el);
});

// 3. Card Spotlight & 3D Tilt Effect
document.querySelectorAll('.product-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const r = card.getBoundingClientRect();
        card.style.setProperty('--mx', `${e.clientX - r.left}px`);
        card.style.setProperty('--my', `${e.clientY - r.top}px`);
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = `translateY(-8px) rotateX(${-y * 7}deg) rotateY(${x * 7}deg)`;
    });
    card.addEventListener('mouseleave', () => {
        card.style.transform = '';
    });
});

// 4. Button Ripple Effect
document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-primary, .btn-outline');
    if (!btn) return;
    const r = document.createElement('span');
    r.className = 'ripple';
    const size = Math.max(btn.clientWidth, btn.clientHeight);
    const rect = btn.getBoundingClientRect();
    r.style.width = r.style.height = size + 'px';
    r.style.left = (e.clientX - rect.left - size/2) + 'px';
    r.style.top = (e.clientY - rect.top - size/2) + 'px';
    btn.appendChild(r);
    setTimeout(() => r.remove(), 600);
});

// 5. Odometer Number Counter
const odoObs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            const el = e.target;
            const target = parseInt(el.dataset.value || '0');
            let start = 0;
            const dur = 1200;
            const t0 = performance.now();
            (function step(now) {
                const p = Math.min((now - t0) / dur, 1);
                el.textContent = Math.floor(p * target).toLocaleString('en-IN') + (el.dataset.suffix || '');
                if (p < 1) requestAnimationFrame(step);
            })(t0);
            odoObs.unobserve(el);
        }
    });
}, { threshold: 0.4 });
document.querySelectorAll('.odometer').forEach(el => odoObs.observe(el));

// 6. Floating Hero Particles Canvas
const canvas = document.getElementById('particleCanvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    let W, H, dots = [];
    const resize = () => {
        W = canvas.width = canvas.offsetWidth;
        H = canvas.height = canvas.offsetHeight;
        dots = Array.from({length: 35}, () => ({
            x: Math.random()*W, y: Math.random()*H,
            r: Math.random()*2+0.8,
            vx: (Math.random()-0.5)*0.4, vy: (Math.random()-0.5)*0.4,
            a: Math.random()*0.5+0.2
        }));
    };
    resize();
    window.addEventListener('resize', resize);
    (function draw() {
        ctx.clearRect(0, 0, W, H);
        dots.forEach(d => {
            d.x += d.vx; d.y += d.vy;
            if (d.x < 0 || d.x > W) d.vx *= -1;
            if (d.y < 0 || d.y > H) d.vy *= -1;
            ctx.beginPath();
            ctx.arc(d.x, d.y, d.r, 0, Math.PI*2);
            ctx.fillStyle = `rgba(255, 107, 53, ${d.a})`;
            ctx.fill();
        });
        requestAnimationFrame(draw);
    })();
}

// 7. Cursor Trail Dots
let lastDot = 0;
document.addEventListener('mousemove', (e) => {
    const now = Date.now();
    if (now - lastDot < 55) return;
    lastDot = now;
    const dot = document.createElement('div');
    dot.className = 'cursor-dot';
    dot.style.left = e.clientX + 'px';
    dot.style.top = e.clientY + 'px';
    document.body.appendChild(dot);
    setTimeout(() => dot.remove(), 700);
});
</script>
</body>
</html>
"""

# ============================================================
# 5. PAGE TEMPLATES
# ============================================================
HOME_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="hero">
    <div class="aurora"></div>
    <div class="ripple-grid"></div>
    <canvas id="particleCanvas"></canvas>
    <div class="container hero-content">
        <span class="badge" style="font-size:0.8rem; padding:6px 14px; margin-bottom:16px;">✨ #1 Creator Digital Marketplace</span>
        <h1 class="hero-title">Better experience<br>for effective <span class="accent">websites</span></h1>
        <p class="hero-subtitle">Discover, buy, and sell high-performance digital templates, UI kits, cyberpunk graphics, and full-stack code assets.</p>
        <div class="hero-cta">
            <a href="{{ url_for('products') }}" class="btn-primary btn-lg">Explore Marketplace →</a>
            <a href="{{ url_for('quick_login', role='seller') }}" class="btn-outline btn-lg">🏪 Try Seller Studio</a>
        </div>
        <div class="hero-stats">
            <div><strong class="odometer" data-value="{{ total_products }}" data-suffix="+">0</strong><span>Approved Assets</span></div>
            <div><strong class="odometer" data-value="{{ total_sellers }}" data-suffix="+">0</strong><span>Verified Creators</span></div>
            <div><strong class="odometer" data-value="1250" data-suffix="+">0</strong><span>Downloads</span></div>
            <div><strong>4.9 ⭐</strong><span>Avg Rating</span></div>
        </div>
    </div>
</section>

<section class="section">
    <div class="container">
        <div class="section-header">
            <h2>🔥 Featured Digital Assets</h2>
            <a href="{{ url_for('products') }}" class="view-all">Browse All Products →</a>
        </div>
        <div class="product-grid">
            {% for p in featured %}
            <div class="product-card">
                <a href="{{ url_for('product_detail', slug=p.slug) }}" class="img-wrap">
                    <img src="{{ p.image }}" alt="{{ p.title }}" loading="lazy">
                </a>
                <div class="product-info">
                    <span class="badge">{{ p.category.name if p.category else 'Asset' }}</span>
                    <a href="{{ url_for('product_detail', slug=p.slug) }}"><h3>{{ p.title }}</h3></a>
                    <p class="seller">By {{ p.seller.username }}</p>
                    <div class="card-footer">
                        <span class="price">₹{{ "%.0f"|format(p.price) }}</span>
                        <form action="{{ url_for('add_to_cart', pid=p.id) }}" method="post">
                            <button type="submit" class="btn-primary" style="padding:7px 14px; font-size:0.8rem;">🛒 Add</button>
                        </form>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<section class="section" style="background: rgba(22,33,62,0.35);">
    <div class="container">
        <div class="section-header">
            <h2>📂 Browse Categories (Hover to Flip)</h2>
        </div>
        <div class="category-grid">
            {% for c in categories %}
            <a href="{{ url_for('products') }}?cat={{ c.id }}" class="flip-card">
                <div class="flip-inner">
                    <div class="flip-face">
                        <span style="font-size:2.4rem; margin-bottom:10px;">{{ c.icon }}</span>
                        <h4>{{ c.name }}</h4>
                        <p style="color:var(--text-dim); font-size:0.8rem;">{{ c.products|length }} items</p>
                    </div>
                    <div class="flip-back flip-face">
                        <h4>{{ c.name }}</h4>
                        <p style="font-size:0.82rem; margin:8px 0;">Explore top-rated {{ c.name }}</p>
                        <span style="font-weight:700; font-size:0.85rem;">View Catalog →</span>
                    </div>
                </div>
            </a>
            {% endfor %}
        </div>
    </div>
</section>
""")

PRODUCTS_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container">
        <div class="section-header">
            <h2>🛍️ Explore Marketplace ({{ products|length }} Assets)</h2>
            <form method="get" action="{{ url_for('products') }}" style="display:flex; gap:10px; flex-wrap:wrap;">
                <select name="cat" style="padding:9px 14px; border-radius:10px; background:var(--bg-card); color:#fff; border:1px solid var(--border);">
                    <option value="">All Categories</option>
                    {% for c in categories %}
                        <option value="{{ c.id }}" {% if request.args.get('cat') == c.id|string %}selected{% endif %}>{{ c.icon }} {{ c.name }}</option>
                    {% endfor %}
                </select>
                <select name="sort" style="padding:9px 14px; border-radius:10px; background:var(--bg-card); color:#fff; border:1px solid var(--border);">
                    <option value="newest" {% if request.args.get('sort')=='newest' %}selected{% endif %}>Newest First</option>
                    <option value="low" {% if request.args.get('sort')=='low' %}selected{% endif %}>Price: Low to High</option>
                    <option value="high" {% if request.args.get('sort')=='high' %}selected{% endif %}>Price: High to Low</option>
                </select>
                <button type="submit" class="btn-primary">Apply Filter</button>
                {% if request.args.get('cat') or request.args.get('sort') or request.args.get('q') %}
                    <a href="{{ url_for('products') }}" class="btn-outline">Reset</a>
                {% endif %}
            </form>
        </div>
        <div class="product-grid">
            {% for p in products %}
            <div class="product-card">
                <a href="{{ url_for('product_detail', slug=p.slug) }}" class="img-wrap">
                    <img src="{{ p.image }}" alt="{{ p.title }}">
                </a>
                <div class="product-info">
                    <span class="badge">{{ p.category.name if p.category else 'General' }}</span>
                    <a href="{{ url_for('product_detail', slug=p.slug) }}"><h3>{{ p.title }}</h3></a>
                    <p class="seller">By {{ p.seller.username }} · ⭐ {{ p.avg_rating() }}</p>
                    <div class="card-footer">
                        <span class="price">₹{{ "%.0f"|format(p.price) }}</span>
                        <form action="{{ url_for('add_to_cart', pid=p.id) }}" method="post">
                            <button type="submit" class="btn-primary" style="padding:7px 14px; font-size:0.8rem;">🛒 Add to Cart</button>
                        </form>
                    </div>
                </div>
            </div>
            {% else %}
            <div style="grid-column: 1/-1; text-align:center; padding:60px 20px; background:var(--bg-card); border-radius:14px;">
                <div style="font-size:3.5rem; margin-bottom:10px;">🔍</div>
                <h3>No matching digital products found</h3>
                <p style="color:var(--text-dim); margin:8px 0 20px;">Try clearing your filters or searching another keyword.</p>
                <a href="{{ url_for('products') }}" class="btn-primary">View All Products</a>
            </div>
            {% endfor %}
        </div>
    </div>
</section>
""")

PRODUCT_DETAIL_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container">
        <p style="margin-bottom:20px; color:var(--text-dim); font-size:0.88rem;">
            <a href="{{ url_for('home') }}">Home</a> › <a href="{{ url_for('products') }}">Products</a> › <span style="color:var(--accent);">{{ product.title }}</span>
        </p>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap:40px; align-items:start;">
            <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:16px; overflow:hidden;">
                <img src="{{ product.image }}" alt="{{ product.title }}" style="width:100%; aspect-ratio:16/10; object-fit:cover;">
            </div>
            <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:16px; padding:32px;">
                <span class="badge">{{ product.category.name if product.category else 'Digital Asset' }}</span>
                <h1 style="font-size:2.1rem; margin:10px 0;">{{ product.title }}</h1>
                <p style="color:var(--text-dim); margin-bottom:18px;">Creator: <strong style="color:#fff;">{{ product.seller.username }}</strong> · ⭐ {{ product.avg_rating() }} ({{ reviews|length }} reviews)</p>
                <div style="font-size:2.3rem; color:var(--accent); font-weight:800; margin:16px 0;">₹{{ "%.0f"|format(product.price) }}</div>
                <p style="color:var(--text-dim); line-height:1.8; margin-bottom:24px;">{{ product.description }}</p>
                
                <div style="background:var(--bg-dark); padding:16px; border-radius:12px; margin-bottom:24px; font-size:0.85rem; color:var(--text-dim);">
                    <div>✅ Instant ZIP / Source Code Download</div>
                    <div>✅ Lifetime Updates & Commercial License</div>
                    <div>✅ Verified Token Security</div>
                </div>

                <form action="{{ url_for('add_to_cart', pid=product.id) }}" method="post" style="display:flex; gap:14px; flex-wrap:wrap;">
                    <button type="submit" class="btn-primary btn-lg" style="flex:1; justify-content:center;">🛒 Add to Cart</button>
                    <a href="{{ url_for('cart') }}" class="btn-outline btn-lg">View Cart →</a>
                </form>
            </div>
        </div>

        <div style="margin-top:60px;">
            <h2 style="margin-bottom:24px;">⭐ Buyer Reviews ({{ reviews|length }})</h2>
            {% if current_user.is_authenticated %}
            <form action="{{ url_for('add_review', pid=product.id) }}" method="post" style="background:var(--bg-card); padding:24px; border-radius:14px; border:1px solid var(--border); margin-bottom:28px;">
                <h4 style="margin-bottom:14px;">Write a Review</h4>
                <div style="display:grid; grid-template-columns: 150px 1fr; gap:14px;">
                    <div class="form-group">
                        <label>Rating (1-5)</label>
                        <select name="rating"><option value="5">⭐⭐⭐⭐⭐ (5)</option><option value="4">⭐⭐⭐⭐ (4)</option><option value="3">⭐⭐⭐ (3)</option></select>
                    </div>
                    <div class="form-group">
                        <label>Your Experience</label>
                        <input type="text" name="comment" placeholder="Awesome UI kit, clean code..." required>
                    </div>
                </div>
                <button type="submit" class="btn-primary">Post Review</button>
            </form>
            {% endif %}

            {% for r in reviews %}
            <div style="background:var(--bg-card); padding:18px 22px; border-radius:12px; border:1px solid var(--border); margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between;">
                    <strong>👤 {{ r.user.username }}</strong>
                    <span style="color:#ffc107;">⭐ {{ r.rating }}/5</span>
                </div>
                <p style="color:var(--text-dim); margin-top:8px;">{{ r.comment }}</p>
            </div>
            {% else %}
            <p style="color:var(--text-dim);">No reviews yet. Be the first to review this digital product!</p>
            {% endfor %}
        </div>
    </div>
</section>
""")

CART_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container">
        <h2 style="margin-bottom:28px;">🛒 Your Shopping Cart</h2>
        {% if items %}
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:30px; align-items:start;">
            <div>
                {% for item in items %}
                <div style="display:flex; gap:16px; align-items:center; background:var(--bg-card); padding:16px; border-radius:14px; border:1px solid var(--border); margin-bottom:14px;">
                    <img src="{{ item.product.image }}" style="width:90px; height:65px; object-fit:cover; border-radius:8px;">
                    <div style="flex:1;">
                        <h4>{{ item.product.title }}</h4>
                        <p style="color:var(--text-dim); font-size:0.85rem;">₹{{ "%.0f"|format(item.product.price) }} × {{ item.quantity }}</p>
                    </div>
                    <strong style="color:var(--accent); font-size:1.1rem;">₹{{ "%.0f"|format(item.product.price * item.quantity) }}</strong>
                    <a href="{{ url_for('remove_from_cart', cid=item.id) }}" class="btn-outline" style="padding:6px 10px; color:var(--danger);">🗑️</a>
                </div>
                {% endfor %}
            </div>
            <div style="background:var(--bg-card); padding:28px; border-radius:14px; border:1px solid var(--border);">
                <h3 style="margin-bottom:18px;">🧾 Order Summary</h3>
                <div style="display:flex; justify-content:space-between; margin-bottom:10px; color:var(--text-dim);">
                    <span>Subtotal</span><span>₹{{ "%.0f"|format(subtotal) }}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:10px; color:var(--text-dim);">
                    <span>GST / Platform Fee (10%)</span><span>₹{{ "%.0f"|format(subtotal * 0.1) }}</span>
                </div>
                <hr style="border-color:var(--border); margin:16px 0;">
                <div style="display:flex; justify-content:space-between; font-size:1.3rem; font-weight:800; margin-bottom:22px;">
                    <span>Total</span><span style="color:var(--accent);">₹{{ "%.0f"|format(subtotal * 1.1) }}</span>
                </div>
                <a href="{{ url_for('checkout') }}" class="btn-primary btn-lg" style="width:100%; justify-content:center;">💳 Proceed to Checkout →</a>
            </div>
        </div>
        {% else %}
        <div style="text-align:center; padding:70px 20px; background:var(--bg-card); border-radius:16px; border:1px solid var(--border);">
            <div style="font-size:4rem; margin-bottom:12px;">🛒</div>
            <h3>Your cart is empty</h3>
            <p style="color:var(--text-dim); margin:8px 0 22px;">Explore top UI kits, templates, and graphics to add to your cart.</p>
            <a href="{{ url_for('products') }}" class="btn-primary btn-lg">Explore Marketplace →</a>
        </div>
        {% endif %}
    </div>
</section>
""")

CHECKOUT_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container" style="max-width:620px;">
        <div style="background:var(--bg-card); padding:36px; border-radius:16px; border:1px solid var(--border);">
            <h2 style="margin-bottom:8px;">💳 Instant Checkout (Sandbox)</h2>
            <p style="color:var(--text-dim); margin-bottom:24px;">Amount Payable: <strong style="color:var(--accent); font-size:1.3rem;">₹{{ "%.0f"|format(total) }}</strong></p>
            
            <form action="{{ url_for('checkout') }}" method="post">
                <div class="form-group">
                    <label>Promo / Coupon Code (Try: <b>SAVE10</b>)</label>
                    <input type="text" name="coupon" placeholder="Enter SAVE10 for 10% discount">
                </div>
                <div class="form-group">
                    <label>Cardholder Name</label>
                    <input type="text" value="{{ current_user.username }}" required>
                </div>
                <div class="form-group">
                    <label>Dummy Card Number</label>
                    <input type="text" value="4242 •••• •••• 4242" required>
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">
                    <div class="form-group"><label>Expiry Date</label><input type="text" value="12/28" required></div>
                    <div class="form-group"><label>CVV</label><input type="password" value="999" required></div>
                </div>
                <button type="submit" class="btn-primary btn-lg" style="width:100%; justify-content:center; margin-top:12px;">
                    ⚡ Complete Order & Generate Download Tokens
                </button>
            </form>
        </div>
    </div>
</section>
""")

ORDER_SUCCESS_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<canvas id="confettiCanvas" style="position:fixed; inset:0; pointer-events:none; z-index:9999;"></canvas>
<section class="section">
    <div class="container" style="max-width:720px; text-align:center;">
        <div style="background:var(--bg-card); padding:44px 32px; border-radius:18px; border:1px solid var(--success);">
            <div style="font-size:4.5rem;">🎉</div>
            <h1 style="color:var(--success); margin:12px 0;">Order Confirmed!</h1>
            <p style="color:var(--text-dim);">Order ID: <strong>#{{ order.id }}</strong> · Total Paid: <strong style="color:var(--accent);">₹{{ "%.0f"|format(order.total) }}</strong></p>

            <div style="background:var(--bg-dark); padding:24px; border-radius:14px; margin-top:28px; text-align:left; border:1px solid var(--border);">
                <h3 style="margin-bottom:16px;">⬇️ Your Token-Verified Digital Downloads</h3>
                {% for d in downloads %}
                <div style="display:flex; justify-content:space-between; align-items:center; padding:14px; background:var(--bg-card); border-radius:10px; margin-bottom:10px; flex-wrap:wrap; gap:10px;">
                    <div>
                        <strong>📦 {{ d.product.title }}</strong>
                        <div style="font-size:0.75rem; color:var(--text-dim);">Token: {{ d.token[:18] }}...</div>
                    </div>
                    <a href="{{ url_for('download_file', token=d.token) }}" class="btn-primary">⬇️ Download Package</a>
                </div>
                {% endfor %}
            </div>

            <div style="margin-top:28px; display:flex; justify-content:center; gap:14px; flex-wrap:wrap;">
                <a href="{{ url_for('my_orders') }}" class="btn-outline">📋 View Order History</a>
                <a href="{{ url_for('products') }}" class="btn-primary">Continue Shopping →</a>
            </div>
        </div>
    </div>
</section>
<script>
// Confetti Blast on Order Success
(function() {
    const c = document.getElementById('confettiCanvas');
    const ctx = c.getContext('2d');
    c.width = innerWidth; c.height = innerHeight;
    const colors = ['#ff6b35', '#2ecc71', '#ffc107', '#9b59ff', '#00d2ff'];
    const parts = Array.from({length: 110}, () => ({
        x: innerWidth/2, y: innerHeight/2,
        vx: (Math.random()-0.5)*16, vy: Math.random()*-16 - 4,
        s: Math.random()*7+4, col: colors[Math.floor(Math.random()*colors.length)],
        a: 1
    }));
    let frame = 0;
    (function loop() {
        frame++;
        ctx.clearRect(0,0,c.width,c.height);
        parts.forEach(p => {
            p.vy += 0.4; p.x += p.vx; p.y += p.vy; p.a -= 0.006;
            ctx.globalAlpha = Math.max(p.a, 0);
            ctx.fillStyle = p.col;
            ctx.fillRect(p.x, p.y, p.s, p.s*1.5);
        });
        if (frame < 180) requestAnimationFrame(loop);
        else c.remove();
    })();
})();
</script>
""")

ABOUT_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container" style="max-width:920px;">
        <!-- HERO -->
        <div style="text-align:center; margin-bottom:50px;">
            <div style="width:130px; height:130px; background:linear-gradient(135deg,#ff6b35,#9b59ff); border-radius:50%; margin:0 auto 22px; display:flex; align-items:center; justify-content:center; font-size:3.8rem; box-shadow:0 18px 50px rgba(255,107,53,0.4);">
                👨‍💻
            </div>
            <span class="badge">Full-Stack Developer & Linux Enthusiast</span>
            <h1 style="font-size:2.7rem; margin:10px 0;">Hi, I'm <span class="accent">Raj Gautam</span></h1>
            <p style="color:var(--text-dim); font-size:1.1rem; max-width:620px; margin:0 auto;">
                Creator of <strong style="color:#ff6b35;">Ilania Digital Marketplace</strong> · BCA Student & Software Developer
            </p>
            <div style="margin-top:22px; display:flex; justify-content:center; gap:12px; flex-wrap:wrap;">
                <a href="https://github.com/Rg100152" target="_blank" class="btn-primary">🐙 GitHub (@Rg100152)</a>
                <a href="{{ url_for('products') }}" class="btn-outline">🛍️ Explore My Marketplace</a>
            </div>
        </div>

        <!-- STORY -->
        <div style="background:var(--bg-card); padding:36px; border-radius:16px; border:1px solid var(--border); margin-bottom:28px;">
            <h2 style="margin-bottom:16px;">📖 About This Project</h2>
            <p style="color:var(--text-dim); line-height:1.85; margin-bottom:14px;">
                I'm <strong style="color:#fff;">Raj Gautam</strong>, a developer passionate about crafting clean dark-themed web interfaces, Python backends, and Linux-first workflows.
            </p>
            <p style="color:var(--text-dim); line-height:1.85;">
                <strong style="color:var(--accent);">Ilania Marketplace</strong> is a complete full-stack digital asset platform built in Python (Flask + SQLAlchemy) where creators can upload templates, UI kits, and code packages, and buyers can purchase and download them with secure token verification.
            </p>
        </div>

        <!-- TECH STACK -->
        <div style="background:var(--bg-card); padding:36px; border-radius:16px; border:1px solid var(--border); margin-bottom:28px;">
            <h2 style="margin-bottom:20px;">💻 Tech Stack & Architecture</h2>
            <div style="display:flex; flex-wrap:wrap; gap:10px;">
                {% for skill in ['Python 3', 'Flask', 'SQLAlchemy ORM', 'SQLite DB', 'Flask-Login', 'Jinja2 Templates', 'HTML5 / CSS3', 'Vanilla JS Animations', 'Pop!_OS Linux', 'Git & GitHub'] %}
                <span style="background:rgba(255,107,53,0.14); color:#ff6b35; border:1px solid rgba(255,107,53,0.3); padding:8px 16px; border-radius:20px; font-size:0.88rem; font-weight:600;">{{ skill }}</span>
                {% endfor %}
            </div>
        </div>

        <!-- STATS -->
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:20px;">
            <div style="background:var(--bg-card); padding:28px; border-radius:16px; text-align:center; border:1px solid var(--border);">
                <h1 style="color:var(--accent); font-size:2.4rem;" class="odometer" data-value="8">0</h1>
                <p style="color:var(--text-dim);">Database Models</p>
            </div>
            <div style="background:var(--bg-card); padding:28px; border-radius:16px; text-align:center; border:1px solid var(--border);">
                <h1 style="color:var(--accent); font-size:2.4rem;" class="odometer" data-value="20" data-suffix="+">0</h1>
                <p style="color:var(--text-dim);">Custom Animations</p>
            </div>
            <div style="background:var(--bg-card); padding:28px; border-radius:16px; text-align:center; border:1px solid var(--border);">
                <h1 style="color:var(--accent); font-size:2.4rem;">100%</h1>
                <p style="color:var(--text-dim);">Single-File Flask Architecture</p>
            </div>
        </div>
    </div>
</section>
""")

LOGIN_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<div class="form-box">
    <h2>🔑 Login to Ilania</h2>
    <form method="post">
        <div class="form-group"><label>Email Address</label><input type="email" name="email" placeholder="buyer@test.com" required></div>
        <div class="form-group"><label>Password</label><input type="password" name="password" placeholder="••••••••" required></div>
        <button type="submit" class="btn-primary btn-lg" style="width:100%; justify-content:center;">Login</button>
    </form>
    <div style="margin-top:22px; padding-top:18px; border-top:1px solid var(--border); font-size:0.82rem; color:var(--text-dim);">
        <strong style="color:#fff; display:block; margin-bottom:8px;">⚡ Instant 1-Click Demo Logins:</strong>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <a href="{{ url_for('quick_login', role='buyer') }}" class="btn-outline" style="padding:6px 12px;">👤 Buyer</a>
            <a href="{{ url_for('quick_login', role='seller') }}" class="btn-outline" style="padding:6px 12px;">🏪 Seller</a>
            <a href="{{ url_for('quick_login', role='admin') }}" class="btn-outline" style="padding:6px 12px;">🛡️ Admin</a>
        </div>
    </div>
    <p style="text-align:center; margin-top:18px; font-size:0.85rem; color:var(--text-dim);">
        New user? <a href="{{ url_for('register') }}" style="color:var(--accent); font-weight:600;">Create an account</a>
    </p>
</div>
""")

REGISTER_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<div class="form-box">
    <h2>📝 Create Account</h2>
    <form method="post">
        <div class="form-group"><label>Username</label><input name="username" placeholder="rajgautam" required></div>
        <div class="form-group"><label>Email</label><input type="email" name="email" placeholder="raj@example.com" required></div>
        <div class="form-group"><label>Password</label><input type="password" name="password" required></div>
        <div class="form-group">
            <label>Account Role</label>
            <select name="role">
                <option value="buyer">🛍️ Buyer (Browse & Purchase Assets)</option>
                <option value="seller">🏪 Seller (Upload & Sell Products)</option>
            </select>
        </div>
        <button type="submit" class="btn-primary btn-lg" style="width:100%; justify-content:center;">Sign Up</button>
    </form>
</div>
""")

PROFILE_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container">
        <h2>👤 My Account Dashboard</h2>
        <div style="background:var(--bg-card); padding:28px; border-radius:16px; border:1px solid var(--border); margin:20px 0;">
            <p><strong>Username:</strong> {{ current_user.username }}</p>
            <p><strong>Email:</strong> {{ current_user.email }}</p>
            <p><strong>Role:</strong> <span class="badge">{{ current_user.role|upper }}</span></p>
            <p><strong>Member Since:</strong> {{ current_user.created_at.strftime('%d %b %Y') }}</p>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
            <a href="{{ url_for('my_orders') }}" class="btn-primary">📋 My Orders</a>
            <a href="{{ url_for('my_downloads') }}" class="btn-outline">⬇️ My Downloads</a>
            {% if current_user.role == 'seller' %}
                <a href="{{ url_for('seller_dashboard') }}" class="btn-outline">🏪 Seller Studio</a>
            {% endif %}
            {% if current_user.role == 'admin' %}
                <a href="{{ url_for('admin_dashboard') }}" class="btn-outline">🛡️ Admin Panel</a>
            {% endif %}
        </div>
    </div>
</section>
""")

MY_ORDERS_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container">
        <h2 style="margin-bottom:24px;">📋 My Orders</h2>
        <table class="table">
            <tr><th>Order ID</th><th>Date</th><th>Total Paid</th><th>Status</th><th>Action</th></tr>
            {% for o in orders %}
            <tr>
                <td><strong>#{{ o.id }}</strong></td>
                <td>{{ o.created_at.strftime('%d %b %Y, %I:%M %p') }}</td>
                <td style="color:var(--accent); font-weight:700;">₹{{ "%.0f"|format(o.total) }}</td>
                <td><span class="badge" style="color:var(--success);">{{ o.status|upper }}</span></td>
                <td><a href="{{ url_for('order_success', oid=o.id) }}" class="btn-outline" style="padding:5px 12px; font-size:0.8rem;">View Receipt & Files</a></td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center; padding:30px; color:var(--text-dim);">No orders placed yet.</td></tr>
            {% endfor %}
        </table>
    </div>
</section>
""")

MY_DOWNLOADS_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container">
        <h2 style="margin-bottom:24px;">⬇️ My Purchased Digital Files</h2>
        {% for d in downloads %}
        <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-card); padding:18px 24px; border-radius:14px; border:1px solid var(--border); margin-bottom:12px; flex-wrap:wrap; gap:12px;">
            <div>
                <h4>📦 {{ d.product.title }}</h4>
                <small style="color:var(--text-dim);">Secure Token: {{ d.token }} · Status: {{ 'Downloaded' if d.downloaded else 'Ready' }}</small>
            </div>
            <a href="{{ url_for('download_file', token=d.token) }}" class="btn-primary">⬇️ Download License & Asset</a>
        </div>
        {% else %}
        <p style="color:var(--text-dim);">No downloads available yet.</p>
        {% endfor %}
    </div>
</section>
""")

SELLER_DASHBOARD_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container">
        <div class="section-header">
            <h2>🏪 Seller Studio ({{ current_user.username }})</h2>
            <a href="{{ url_for('add_product') }}" class="btn-primary">➕ Upload New Digital Product</a>
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:20px; margin-bottom:36px;">
            <div style="background:var(--bg-card); padding:26px; border-radius:14px; border:1px solid var(--border); text-align:center;">
                <h1 style="color:var(--accent); font-size:2.3rem;">{{ products|length }}</h1>
                <p style="color:var(--text-dim);">Uploaded Products</p>
            </div>
            <div style="background:var(--bg-card); padding:26px; border-radius:14px; border:1px solid var(--border); text-align:center;">
                <h1 style="color:var(--accent); font-size:2.3rem;">{{ total_sales }}</h1>
                <p style="color:var(--text-dim);">Total Units Sold</p>
            </div>
            <div style="background:var(--bg-card); padding:26px; border-radius:14px; border:1px solid var(--border); text-align:center;">
                <h1 style="color:var(--success); font-size:2.3rem;">₹{{ "%.0f"|format(revenue) }}</h1>
                <p style="color:var(--text-dim);">Total Creator Earnings</p>
            </div>
        </div>

        <h3 style="margin-bottom:16px;">📦 My Product Listings</h3>
        <table class="table">
            <tr><th>Title</th><th>Category</th><th>Price</th><th>Approval Status</th><th>Action</th></tr>
            {% for p in products %}
            <tr>
                <td><strong>{{ p.title }}</strong></td>
                <td>{{ p.category.name if p.category else 'General' }}</td>
                <td>₹{{ "%.0f"|format(p.price) }}</td>
                <td><span class="badge">{{ p.status|upper }}</span></td>
                <td><a href="{{ url_for('delete_product', pid=p.id) }}" style="color:var(--danger); font-weight:600;">🗑️ Delete</a></td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center; color:var(--text-dim);">No products uploaded yet.</td></tr>
            {% endfor %}
        </table>
    </div>
</section>
""")

ADD_PRODUCT_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<div class="form-box" style="max-width:600px;">
    <h2>➕ Upload Digital Product</h2>
    <form method="post" enctype="multipart/form-data">
        <div class="form-group"><label>Product Title</label><input name="title" placeholder="e.g., Cyberpunk Neon UI Kit" required></div>
        <div class="form-group">
            <label>Category</label>
            <select name="category_id">
                {% for c in categories %}<option value="{{ c.id }}">{{ c.icon }} {{ c.name }}</option>{% endfor %}
            </select>
        </div>
        <div class="form-group"><label>Price (₹ INR)</label><input type="number" name="price" step="1" value="1499" required></div>
        <div class="form-group"><label>Image URL (or leave blank for auto cover)</label><input name="image_url" placeholder="https://images.unsplash.com/..."></div>
        <div class="form-group"><label>Description</label><textarea name="description" rows="3" required placeholder="Full details, included files, license info..."></textarea></div>
        <button type="submit" class="btn-primary btn-lg" style="width:100%; justify-content:center;">Submit Product for Approval</button>
    </form>
</div>
""")

ADMIN_DASHBOARD_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<section class="section">
    <div class="container">
        <h2 style="margin-bottom:24px;">🛡️ Admin Control Panel</h2>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:20px; margin-bottom:36px;">
            <div style="background:var(--bg-card); padding:24px; border-radius:14px; border:1px solid var(--border); text-align:center;">
                <h1 style="color:var(--accent);">{{ users }}</h1><p style="color:var(--text-dim);">Total Users</p>
            </div>
            <div style="background:var(--bg-card); padding:24px; border-radius:14px; border:1px solid var(--border); text-align:center;">
                <h1 style="color:var(--accent);">{{ products }}</h1><p style="color:var(--text-dim);">Total Products</p>
            </div>
            <div style="background:var(--bg-card); padding:24px; border-radius:14px; border:1px solid var(--border); text-align:center;">
                <h1 style="color:var(--success);">{{ orders }}</h1><p style="color:var(--text-dim);">Completed Orders</p>
            </div>
        </div>

        <h3 style="margin-bottom:16px;">⏳ Pending Product Approvals ({{ pending|length }})</h3>
        <table class="table">
            <tr><th>Product Title</th><th>Creator</th><th>Price</th><th>Decision</th></tr>
            {% for p in pending %}
            <tr>
                <td><strong>{{ p.title }}</strong></td>
                <td>{{ p.seller.username }}</td>
                <td>₹{{ "%.0f"|format(p.price) }}</td>
                <td>
                    <a href="{{ url_for('approve_product', pid=p.id) }}" class="btn-primary" style="padding:6px 12px; font-size:0.78rem; background:var(--success);">✅ Approve</a>
                    <a href="{{ url_for('reject_product', pid=p.id) }}" class="btn-outline" style="padding:6px 12px; font-size:0.78rem; color:var(--danger);">❌ Reject</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align:center; padding:24px; color:var(--text-dim);">🎉 All products have been reviewed!</td></tr>
            {% endfor %}
        </table>
    </div>
</section>
""")

# ============================================================
# 6. APPLICATION ROUTES
# ============================================================
@app.context_processor
def inject_globals():
    count = CartItem.query.filter_by(user_id=current_user.id).count() if current_user.is_authenticated else 0
    return dict(cart_count=count)

@app.route('/')
def home():
    featured = Product.query.filter_by(status='approved').limit(8).all()
    return render_template_string(HOME_HTML,
        featured=featured,
        categories=Category.query.all(),
        total_products=Product.query.filter_by(status='approved').count(),
        total_sellers=User.query.filter_by(role='seller').count()
    )

@app.route('/products/')
def products():
    cat = request.args.get('cat')
    sort = request.args.get('sort', 'newest')
    q = Product.query.filter_by(status='approved')
    if cat:
        q = q.filter_by(category_id=cat)
    if sort == 'low':
        q = q.order_by(Product.price.asc())
    elif sort == 'high':
        q = q.order_by(Product.price.desc())
    else:
        q = q.order_by(Product.id.desc())
    return render_template_string(PRODUCTS_HTML, products=q.all(), categories=Category.query.all())

@app.route('/search/')
def search():
    q = request.args.get('q', '').strip()
    items = Product.query.filter(Product.status == 'approved', Product.title.ilike(f'%{q}%')).all()
    return render_template_string(PRODUCTS_HTML, products=items, categories=Category.query.all())

@app.route('/product/<slug>/')
def product_detail(slug):
    p = Product.query.filter_by(slug=slug).first_or_404()
    reviews = Review.query.filter_by(product_id=p.id).order_by(Review.id.desc()).all()
    return render_template_string(PRODUCT_DETAIL_HTML, product=p, reviews=reviews)

@app.route('/product/<int:pid>/review/', methods=['POST'])
@login_required
def add_review(pid):
    r = Review(product_id=pid, user_id=current_user.id,
               rating=int(request.form.get('rating', 5)),
               comment=request.form.get('comment', ''))
    db.session.add(r)
    db.session.commit()
    flash('⭐ Thank you! Your review has been published.', 'success')
    return redirect(request.referrer or url_for('home'))

@app.route('/about/')
def about():
    return render_template_string(ABOUT_HTML)

# ---- CART & CHECKOUT ----
@app.route('/cart/')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(i.product.price * i.quantity for i in items)
    return render_template_string(CART_HTML, items=items, subtotal=subtotal)

@app.route('/cart/add/<int:pid>/', methods=['POST'])
@login_required
def add_to_cart(pid):
    existing = CartItem.query.filter_by(user_id=current_user.id, product_id=pid).first()
    if existing:
        existing.quantity += 1
    else:
        db.session.add(CartItem(user_id=current_user.id, product_id=pid))
    db.session.commit()
    flash('✅ Added to your shopping cart!', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/remove/<int:cid>/')
@login_required
def remove_from_cart(cid):
    CartItem.query.filter_by(id=cid, user_id=current_user.id).delete()
    db.session.commit()
    flash('🗑️ Item removed from cart.', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout/', methods=['GET', 'POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('products'))
    subtotal = sum(i.product.price * i.quantity for i in items)
    total = subtotal * 1.1
    if request.method == 'POST':
        coupon = request.form.get('coupon', '').strip().upper()
        if coupon == 'SAVE10':
            total = total * 0.90
            flash('🎉 Promo code SAVE10 applied! You saved 10%.', 'success')
        order = Order(user_id=current_user.id, total=total, status='paid')
        db.session.add(order)
        db.session.flush()
        for i in items:
            db.session.add(OrderItem(order_id=order.id, product_id=i.product_id, price=i.product.price, quantity=i.quantity))
            db.session.add(Download(order_id=order.id, product_id=i.product_id, user_id=current_user.id, token=uuid.uuid4().hex))
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return redirect(url_for('order_success', oid=order.id))
    return render_template_string(CHECKOUT_HTML, total=total)

@app.route('/order/success/<int:oid>/')
@login_required
def order_success(oid):
    order = Order.query.filter_by(id=oid, user_id=current_user.id).first_or_404()
    downloads = Download.query.filter_by(order_id=oid).all()
    return render_template_string(ORDER_SUCCESS_HTML, order=order, downloads=downloads)

@app.route('/download/<token>/')
@login_required
def download_file(token):
    d = Download.query.filter_by(token=token, user_id=current_user.id).first_or_404()
    d.downloaded = True
    db.session.commit()
    content = (
        f"====================================================\n"
        f"ILANIA DIGITAL MARKETPLACE — LICENSE & ASSET PACKAGE\n"
        f"====================================================\n"
        f"Product Title : {d.product.title}\n"
        f"Buyer         : {current_user.username} ({current_user.email})\n"
        f"Order ID      : #{d.order_id}\n"
        f"Verify Token  : {d.token}\n"
        f"Downloaded At : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Creator       : Raj Gautam (@Rg100152)\n"
        f"====================================================\n"
        f"Thank you for purchasing on Ilania Digital Marketplace!\n"
    )
    filename = f"{d.product.slug}-package.txt"
    return Response(content, mimetype="text/plain", headers={"Content-Disposition": f"attachment;filename={filename}"})

# ---- USER ACCOUNT ----
@app.route('/account/profile/')
@login_required
def profile():
    return render_template_string(PROFILE_HTML)

@app.route('/account/orders/')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    return render_template_string(MY_ORDERS_HTML, orders=orders)

@app.route('/account/downloads/')
@login_required
def my_downloads():
    downloads = Download.query.filter_by(user_id=current_user.id).order_by(Download.id.desc()).all()
    return render_template_string(MY_DOWNLOADS_HTML, downloads=downloads)

# ---- SELLER STUDIO ----
@app.route('/seller/')
@login_required
def seller_dashboard():
    if current_user.role not in ('seller', 'admin'):
        flash('Switch to a Seller account to access Seller Studio.', 'error')
        return redirect(url_for('home'))
    products = Product.query.filter_by(seller_id=current_user.id).all()
    total_sales = sum(o.quantity for p in products for o in OrderItem.query.filter_by(product_id=p.id).all())
    revenue = sum(o.price * o.quantity for p in products for o in OrderItem.query.filter_by(product_id=p.id).all())
    return render_template_string(SELLER_DASHBOARD_HTML, products=products, total_sales=total_sales, revenue=revenue)

@app.route('/seller/product/add/', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role not in ('seller', 'admin'):
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        slug = title.lower().replace(' ', '-') + '-' + str(random.randint(100, 999))
        img_url = request.form.get('image_url', '').strip()
        if not img_url:
            img_url = "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=800&q=80"
        p = Product(
            seller_id=current_user.id,
            category_id=request.form['category_id'],
            title=title, slug=slug,
            description=request.form['description'],
            price=float(request.form['price']),
            image=img_url,
            status='pending'
        )
        db.session.add(p)
        db.session.commit()
        flash('🚀 Product submitted! Switch to Admin to approve it.', 'success')
        return redirect(url_for('seller_dashboard'))
    return render_template_string(ADD_PRODUCT_HTML, categories=Category.query.all())

@app.route('/seller/product/delete/<int:pid>/')
@login_required
def delete_product(pid):
    Product.query.filter_by(id=pid, seller_id=current_user.id).delete()
    db.session.commit()
    flash('🗑️ Product listing deleted.', 'success')
    return redirect(url_for('seller_dashboard'))

# ---- ADMIN PANEL ----
@app.route('/admin-panel/')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Admin access required!', 'error')
        return redirect(url_for('home'))
    return render_template_string(ADMIN_DASHBOARD_HTML,
        users=User.query.count(),
        products=Product.query.count(),
        orders=Order.query.count(),
        pending=Product.query.filter_by(status='pending').all()
    )

@app.route('/admin-panel/approve/<int:pid>/')
@login_required
def approve_product(pid):
    if current_user.role != 'admin':
        abort(403)
    p = Product.query.get_or_404(pid)
    p.status = 'approved'
    db.session.commit()
    flash(f'✅ Approved "{p.title}"! It is now live.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin-panel/reject/<int:pid>/')
@login_required
def reject_product(pid):
    if current_user.role != 'admin':
        abort(403)
    p = Product.query.get_or_404(pid)
    p.status = 'rejected'
    db.session.commit()
    flash(f'❌ Rejected "{p.title}".', 'error')
    return redirect(url_for('admin_dashboard'))

# ---- AUTHENTICATION & 1-CLICK DEMO SWITCH ----
@app.route('/quick-login/<role>/')
def quick_login(role):
    email_map = {
        'buyer': 'buyer@test.com',
        'seller': 'seller@test.com',
        'admin': 'admin@test.com'
    }
    u = User.query.filter_by(email=email_map.get(role, 'buyer@test.com')).first()
    if u:
        login_user(u)
        flash(f'⚡ Switched to Demo {u.role.upper()} Account ({u.username})!', 'success')
    return redirect(request.referrer or url_for('home'))

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        u = User(
            username=request.form['username'],
            email=request.form['email'],
            password=generate_password_hash(request.form['password']),
            role=request.form.get('role', 'buyer')
        )
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash('🎉 Welcome to Ilania Marketplace!', 'success')
        return redirect(url_for('home'))
    return render_template_string(REGISTER_HTML)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(email=request.form['email']).first()
        if u and check_password_hash(u.password, request.form['password']):
            login_user(u)
            flash(f'Welcome back, {u.username}!', 'success')
            return redirect(url_for('home'))
        flash('Invalid email or password', 'error')
    return render_template_string(LOGIN_HTML)

@app.route('/logout/')
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

# ============================================================
# 7. AUTO-SEED DEMO DATA
# ============================================================
def seed_database():
    if User.query.count() > 0:
        return
    admin = User(username='RajAdmin', email='admin@test.com', password=generate_password_hash('admin123'), role='admin')
    seller = User(username='ArenaStudio', email='seller@test.com', password=generate_password_hash('seller123'), role='seller')
    buyer = User(username='DemoBuyer', email='buyer@test.com', password=generate_password_hash('buyer123'), role='buyer')
    db.session.add_all([admin, seller, buyer])
    db.session.commit()

    cat_data = [
        ('Templates', 'templates', '📄'),
        ('UI Kits', 'ui-kits', '🎨'),
        ('Graphics', 'graphics', '🖼️'),
        ('Courses', 'courses', '🎓'),
        ('Fonts', 'fonts', '🔤'),
        ('Icons', 'icons', '✨'),
    ]
    cats = []
    for name, slug, icon in cat_data:
        c = Category(name=name, slug=slug, icon=icon)
        db.session.add(c)
        cats.append(c)
    db.session.commit()

    products_seed = [
        ('Knight Cyberpunk UI Kit', 2500, cats[1].id, 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80', 'approved',
         'Complete 80+ dark-theme Figma & HTML/CSS screens for modern dashboards and SaaS web apps.'),
        ('Arena 3D Abstract Graphic Pack', 1800, cats[2].id, 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80', 'approved',
         'High-resolution 4K neon glassmorphism renders, meshes, and hero backgrounds.'),
        ('Ilania Pro SaaS Landing Template', 3200, cats[0].id, 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80', 'approved',
         'Responsive dark-mode startup template with 20+ micro-animations and clean code.'),
        ('Samurai Game Asset & HUD Pack', 999, cats[2].id, 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=800&q=80', 'approved',
         'Cyberpunk samurai UI elements, health bars, weapon icons, and sound effects.'),
        ('Python & Flask Full-Stack Bootcamp', 1499, cats[3].id, 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?auto=format&fit=crop&w=800&q=80', 'approved',
         'Master Flask, SQLAlchemy, authentication, and deployment with real-world projects.'),
        ('Pixel Neon Vector Icon Set (500+)', 650, cats[5].id, 'https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?auto=format&fit=crop&w=800&q=80', 'approved',
         '500+ customizable SVG & PNG glowing icons for dark-mode interfaces.'),
        ('Nova Geometric Display Font', 1200, cats[4].id, 'https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=800&q=80', 'pending',
         'Modern futuristic typeface for headings, logos, and gaming banners (Pending Admin Approval).')
    ]
    for title, price, cid, img, status, desc in products_seed:
        p = Product(
            seller_id=seller.id, category_id=cid, title=title,
            slug=title.lower().replace(' ', '-').replace('&', 'and').replace('(', '').replace(')', '').replace('+', ''),
            description=desc, price=price, image=img, status=status
        )
        db.session.add(p)
    db.session.commit()

    first_prod = Product.query.first()
    db.session.add(Review(product_id=first_prod.id, user_id=buyer.id, rating=5, comment="Best dark UI kit! Saved me days of frontend work."))
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_database()

if __name__ == '__main__':
    print("\n" + "="*58)
    print("🚀 ILANIA DIGITAL MARKETPLACE (FLASK) IS LIVE!")
    print("="*58)
    print("🔗 Local URL : http://127.0.0.1:5000")
    print("👨‍💻 Creator   : Raj Gautam (@Rg100152)")
    print("\n🔑 Demo Accounts (or use 1-Click buttons in Footer):")
    print("   • Admin  : admin@test.com  / admin123")
    print("   • Seller : seller@test.com / seller123")
    print("   • Buyer  : buyer@test.com  / buyer123")
    print("="*58 + "\n")
    app.run(debug=True, port=5000)
