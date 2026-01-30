"""
Grant Applicant Vetting Tool - Flask Application

Main application file that provides:
- Web dashboard for managing applicants
- REST API for programmatic access
- Background job processing for scraping
"""

import os
import json
import threading
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, redirect,
    url_for, flash, send_file
)

from models import (
    db, Applicant, SocialProfile, ContentItem,
    Flag, SanctionsCheck, VettingReport
)

from scrapers import NostrScraper, TwitterScraper, WebScraper, InstagramScraper
from scrapers.discovery import ProfileDiscoveryEngine, DiscoveredProfile

from analyzers import GuidelinesAnalyzer, KeywordAnalyzer
from analyzers.sanctions import OFACSanctionsChecker

from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize components
guidelines_analyzer = GuidelinesAnalyzer()
sanctions_checker = OFACSanctionsChecker()
discovery_engine = ProfileDiscoveryEngine()

# Initialize scrapers (they'll check for API keys internally)
scrapers = {
    'nostr': NostrScraper(),
    'twitter': TwitterScraper(),
    'instagram': InstagramScraper(),
    'web': WebScraper(),
}


# ============================================================================
# Database initialization
# ============================================================================

@app.before_request
def create_tables():
    """Create database tables on first request."""
    db.create_all()


# ============================================================================
# Dashboard Routes
# ============================================================================

@app.route('/')
def dashboard():
    """Main dashboard showing overview of all applicants."""
    # Get statistics
    total_applicants = Applicant.query.count()
    pending_applicants = Applicant.query.filter_by(status='pending').count()
    in_progress = Applicant.query.filter_by(status='in_progress').count()
    passed = Applicant.query.filter_by(status='passed').count()
    failed = Applicant.query.filter_by(status='failed').count()
    needs_review = Applicant.query.filter_by(status='needs_review').count()

    # Get recent applicants
    recent_applicants = Applicant.query.order_by(
        Applicant.created_at.desc()
    ).limit(10).all()

    # Get high-risk applicants
    high_risk = Applicant.query.filter(
        Applicant.risk_level.in_(['high', 'critical'])
    ).order_by(Applicant.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
        total_applicants=total_applicants,
        pending_applicants=pending_applicants,
        in_progress=in_progress,
        passed=passed,
        failed=failed,
        needs_review=needs_review,
        recent_applicants=recent_applicants,
        high_risk=high_risk
    )


@app.route('/applicants')
def list_applicants():
    """List all applicants with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', None)
    risk_filter = request.args.get('risk_level', None)
    search = request.args.get('search', None)

    query = Applicant.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if risk_filter:
        query = query.filter_by(risk_level=risk_filter)
    if search:
        query = query.filter(
            Applicant.name.ilike(f'%{search}%') |
            Applicant.email.ilike(f'%{search}%') |
            Applicant.organization.ilike(f'%{search}%')
        )

    pagination = query.order_by(Applicant.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('applicants.html',
        applicants=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        risk_filter=risk_filter,
        search=search
    )


@app.route('/applicants/new', methods=['GET', 'POST'])
def new_applicant():
    """Create a new applicant."""
    if request.method == 'POST':
        data = request.form

        applicant = Applicant(
            name=data.get('name'),
            email=data.get('email'),
            organization=data.get('organization'),
            country=data.get('country'),
            notes=data.get('notes'),
            status='pending'
        )
        db.session.add(applicant)
        db.session.flush()  # Get the ID

        # Add social profiles
        platforms = ['twitter', 'nostr', 'instagram', 'linkedin', 'blog']
        for platform in platforms:
            handle = data.get(f'{platform}_handle')
            url = data.get(f'{platform}_url')
            if handle or url:
                profile = SocialProfile(
                    applicant_id=applicant.id,
                    platform=platform,
                    username=handle,
                    url=url,
                    discovery_method='provided'
                )
                db.session.add(profile)

        db.session.commit()

        flash(f'Applicant "{applicant.name}" created successfully.', 'success')
        return redirect(url_for('view_applicant', applicant_id=applicant.id))

    return render_template('new_applicant.html')


@app.route('/applicants/<int:applicant_id>')
def view_applicant(applicant_id):
    """View detailed information for an applicant."""
    applicant = Applicant.query.get_or_404(applicant_id)

    # Get flags grouped by category
    flags_by_category = {}
    for flag in applicant.flags:
        if flag.category not in flags_by_category:
            flags_by_category[flag.category] = []
        flags_by_category[flag.category].append(flag)

    # Get content items by platform
    content_by_platform = {}
    for item in applicant.content_items:
        if item.platform not in content_by_platform:
            content_by_platform[item.platform] = []
        content_by_platform[item.platform].append(item)

    return render_template('applicant_detail.html',
        applicant=applicant,
        flags_by_category=flags_by_category,
        content_by_platform=content_by_platform
    )


@app.route('/applicants/<int:applicant_id>/edit', methods=['GET', 'POST'])
def edit_applicant(applicant_id):
    """Edit an applicant's information."""
    applicant = Applicant.query.get_or_404(applicant_id)

    if request.method == 'POST':
        data = request.form
        applicant.name = data.get('name', applicant.name)
        applicant.email = data.get('email', applicant.email)
        applicant.organization = data.get('organization', applicant.organization)
        applicant.country = data.get('country', applicant.country)
        applicant.notes = data.get('notes', applicant.notes)

        db.session.commit()
        flash('Applicant updated successfully.', 'success')
        return redirect(url_for('view_applicant', applicant_id=applicant_id))

    return render_template('edit_applicant.html', applicant=applicant)


@app.route('/applicants/<int:applicant_id>/delete', methods=['POST'])
def delete_applicant(applicant_id):
    """Delete an applicant."""
    applicant = Applicant.query.get_or_404(applicant_id)
    name = applicant.name
    db.session.delete(applicant)
    db.session.commit()
    flash(f'Applicant "{name}" deleted.', 'success')
    return redirect(url_for('list_applicants'))


@app.route('/applicants/<int:applicant_id>/status', methods=['POST'])
def update_status(applicant_id):
    """Update an applicant's vetting status."""
    applicant = Applicant.query.get_or_404(applicant_id)
    new_status = request.form.get('status')

    if new_status in ['pending', 'in_progress', 'passed', 'failed', 'needs_review']:
        applicant.status = new_status
        if new_status in ['passed', 'failed']:
            applicant.vetted_at = datetime.utcnow()
        db.session.commit()
        flash(f'Status updated to {new_status}.', 'success')

    return redirect(url_for('view_applicant', applicant_id=applicant_id))


# ============================================================================
# Vetting Actions
# ============================================================================

@app.route('/applicants/<int:applicant_id>/scrape', methods=['POST'])
def scrape_applicant(applicant_id):
    """Start scraping all social profiles for an applicant."""
    applicant = Applicant.query.get_or_404(applicant_id)

    # Update status
    applicant.status = 'in_progress'
    db.session.commit()

    # Run scraping in background thread
    thread = threading.Thread(
        target=_scrape_applicant_task,
        args=(app._get_current_object(), applicant_id)
    )
    thread.daemon = True
    thread.start()

    flash('Scraping started. This may take a few minutes.', 'info')
    return redirect(url_for('view_applicant', applicant_id=applicant_id))


def _scrape_applicant_task(app, applicant_id):
    """Background task to scrape an applicant's profiles."""
    with app.app_context():
        applicant = Applicant.query.get(applicant_id)
        if not applicant:
            return

        for profile in applicant.social_profiles:
            try:
                profile.scrape_status = 'in_progress'
                db.session.commit()

                scraper = scrapers.get(profile.platform)
                if not scraper:
                    profile.scrape_status = 'failed'
                    profile.scrape_error = f'No scraper for platform: {profile.platform}'
                    db.session.commit()
                    continue

                # Determine identifier
                identifier = profile.username or profile.url or profile.platform_id
                if not identifier:
                    profile.scrape_status = 'failed'
                    profile.scrape_error = 'No identifier available'
                    db.session.commit()
                    continue

                # Scrape profile and content
                result = scraper.scrape_all(identifier, limit=200)

                if result.success:
                    # Update profile data
                    if result.profile_data:
                        profile.display_name = result.profile_data.get('display_name')
                        profile.bio = result.profile_data.get('bio')
                        profile.followers_count = result.profile_data.get('followers_count')
                        profile.following_count = result.profile_data.get('following_count')
                        profile.posts_count = result.profile_data.get('posts_count')
                        profile.profile_image_url = result.profile_data.get('profile_image_url')

                    # Save content items
                    for item_data in result.content_items:
                        content_item = ContentItem(
                            applicant_id=applicant_id,
                            social_profile_id=profile.id,
                            content_type=item_data.get('content_type', 'post'),
                            platform=profile.platform,
                            platform_content_id=item_data.get('platform_content_id'),
                            url=item_data.get('url'),
                            text_content=item_data.get('text_content'),
                            raw_content=item_data.get('raw_content'),
                            published_at=datetime.fromisoformat(item_data['published_at']) if item_data.get('published_at') else None,
                            likes_count=item_data.get('likes_count'),
                            reposts_count=item_data.get('reposts_count'),
                            replies_count=item_data.get('replies_count'),
                            media_urls=item_data.get('media_urls')
                        )
                        db.session.add(content_item)

                    profile.scrape_status = 'completed'
                    profile.last_scraped_at = datetime.utcnow()
                else:
                    profile.scrape_status = 'failed'
                    profile.scrape_error = result.error_message

                db.session.commit()

            except Exception as e:
                profile.scrape_status = 'failed'
                profile.scrape_error = str(e)
                db.session.commit()

        # After scraping, run discovery
        _discover_profiles_task(app, applicant_id)


def _discover_profiles_task(app, applicant_id):
    """Discover additional social profiles for an applicant."""
    with app.app_context():
        applicant = Applicant.query.get(applicant_id)
        if not applicant:
            return

        known_profiles = [
            {
                'platform': p.platform,
                'username': p.username,
                'url': p.url,
                'bio': p.bio
            }
            for p in applicant.social_profiles
        ]

        discovered = discovery_engine.discover_profiles(
            name=applicant.name,
            known_profiles=known_profiles,
            email=applicant.email
        )

        for disc in discovered:
            # Check if we already have this profile
            existing = SocialProfile.query.filter_by(
                applicant_id=applicant_id,
                platform=disc.platform,
                username=disc.username
            ).first()

            if not existing:
                profile = SocialProfile(
                    applicant_id=applicant_id,
                    platform=disc.platform,
                    username=disc.username,
                    url=disc.url,
                    discovery_method='discovered'
                )
                db.session.add(profile)

        db.session.commit()


@app.route('/applicants/<int:applicant_id>/analyze', methods=['POST'])
def analyze_applicant(applicant_id):
    """Run content analysis on an applicant."""
    applicant = Applicant.query.get_or_404(applicant_id)

    # Get all content items
    content_items = [
        {
            'text_content': item.text_content,
            'platform': item.platform,
            'url': item.url,
            'published_at': item.published_at.isoformat() if item.published_at else None
        }
        for item in applicant.content_items
        if item.text_content
    ]

    # Get social profiles for bio analysis
    social_profiles = [
        {
            'platform': p.platform,
            'bio': p.bio,
            'url': p.url
        }
        for p in applicant.social_profiles
    ]

    # Run analysis
    result = guidelines_analyzer.analyze_applicant(
        applicant_data={
            'id': applicant.id,
            'name': applicant.name,
            'country': applicant.country
        },
        content_items=content_items,
        social_profiles=social_profiles
    )

    # Clear existing flags
    Flag.query.filter_by(applicant_id=applicant_id).delete()

    # Save new flags
    for flag_data in result.flags:
        flag = Flag(
            applicant_id=applicant_id,
            category=flag_data.category,
            severity=flag_data.severity,
            title=flag_data.title,
            description=flag_data.description,
            matched_keywords=flag_data.matched_keywords,
            evidence_snippet=flag_data.evidence_snippet,
            detection_method='keyword'
        )
        db.session.add(flag)

    # Update applicant risk level
    applicant.risk_level = result.risk_level

    # Set status based on recommendation
    if result.recommendation == 'reject':
        applicant.status = 'failed'
    elif result.recommendation == 'approve' and result.risk_level == 'low':
        applicant.status = 'passed'
    else:
        applicant.status = 'needs_review'

    db.session.commit()

    flash(f'Analysis complete. Risk level: {result.risk_level}', 'info')
    return redirect(url_for('view_applicant', applicant_id=applicant_id))


@app.route('/applicants/<int:applicant_id>/sanctions', methods=['POST'])
def check_sanctions(applicant_id):
    """Check an applicant against OFAC sanctions list."""
    applicant = Applicant.query.get_or_404(applicant_id)

    result = sanctions_checker.check_individual(
        name=applicant.name,
        country=applicant.country
    )

    # Save or update sanctions check
    existing = SanctionsCheck.query.filter_by(applicant_id=applicant_id).first()
    if existing:
        existing.status = 'completed'
        existing.has_matches = result.has_matches
        existing.matches = [m.to_dict() for m in result.matches]
        existing.search_name = result.search_name
        existing.search_country = result.search_country
        existing.checked_at = datetime.utcnow()
    else:
        check = SanctionsCheck(
            applicant_id=applicant_id,
            status='completed',
            has_matches=result.has_matches,
            matches=[m.to_dict() for m in result.matches],
            search_name=result.search_name,
            search_country=result.search_country,
            checked_at=datetime.utcnow()
        )
        db.session.add(check)

    # Create flag if matches found
    if result.has_matches:
        flag = Flag(
            applicant_id=applicant_id,
            category='sanctions',
            severity='critical',
            title='OFAC Sanctions Match',
            description=f'Found {len(result.matches)} potential match(es) in OFAC sanctions list.',
            evidence_snippet=result.matches[0].name if result.matches else None,
            detection_method='sanctions_api'
        )
        db.session.add(flag)

        applicant.risk_level = 'critical'
        applicant.status = 'failed'

    db.session.commit()

    if result.has_matches:
        flash(f'WARNING: Found {len(result.matches)} potential sanctions match(es)!', 'danger')
    else:
        flash('No sanctions matches found.', 'success')

    return redirect(url_for('view_applicant', applicant_id=applicant_id))


@app.route('/applicants/<int:applicant_id>/full-vet', methods=['POST'])
def full_vet(applicant_id):
    """Run full vetting process: scrape, analyze, and sanctions check."""
    applicant = Applicant.query.get_or_404(applicant_id)
    applicant.status = 'in_progress'
    db.session.commit()

    # Run full vetting in background
    thread = threading.Thread(
        target=_full_vet_task,
        args=(app._get_current_object(), applicant_id)
    )
    thread.daemon = True
    thread.start()

    flash('Full vetting started. This may take several minutes.', 'info')
    return redirect(url_for('view_applicant', applicant_id=applicant_id))


def _full_vet_task(app, applicant_id):
    """Background task for full vetting."""
    with app.app_context():
        # 1. Scrape profiles
        _scrape_applicant_task(app, applicant_id)

        # 2. Run analysis
        applicant = Applicant.query.get(applicant_id)
        if not applicant:
            return

        content_items = [
            {
                'text_content': item.text_content,
                'platform': item.platform,
                'url': item.url,
                'published_at': item.published_at.isoformat() if item.published_at else None
            }
            for item in applicant.content_items
            if item.text_content
        ]

        result = guidelines_analyzer.analyze_applicant(
            applicant_data={
                'id': applicant.id,
                'name': applicant.name,
                'country': applicant.country
            },
            content_items=content_items,
            social_profiles=[
                {'platform': p.platform, 'bio': p.bio, 'url': p.url}
                for p in applicant.social_profiles
            ]
        )

        # Save flags
        for flag_data in result.flags:
            flag = Flag(
                applicant_id=applicant_id,
                category=flag_data.category,
                severity=flag_data.severity,
                title=flag_data.title,
                description=flag_data.description,
                matched_keywords=flag_data.matched_keywords,
                evidence_snippet=flag_data.evidence_snippet,
                detection_method='keyword'
            )
            db.session.add(flag)

        # 3. Sanctions check
        sanctions_result = sanctions_checker.check_individual(
            name=applicant.name,
            country=applicant.country
        )

        check = SanctionsCheck(
            applicant_id=applicant_id,
            status='completed',
            has_matches=sanctions_result.has_matches,
            matches=[m.to_dict() for m in sanctions_result.matches],
            search_name=sanctions_result.search_name,
            search_country=sanctions_result.search_country,
            checked_at=datetime.utcnow()
        )
        db.session.add(check)

        if sanctions_result.has_matches:
            flag = Flag(
                applicant_id=applicant_id,
                category='sanctions',
                severity='critical',
                title='OFAC Sanctions Match',
                description=f'Found {len(sanctions_result.matches)} potential match(es).',
                detection_method='sanctions_api'
            )
            db.session.add(flag)
            applicant.risk_level = 'critical'
            applicant.status = 'failed'
        else:
            applicant.risk_level = result.risk_level
            if result.recommendation == 'reject':
                applicant.status = 'failed'
            elif result.recommendation == 'approve' and result.risk_level == 'low':
                applicant.status = 'passed'
            else:
                applicant.status = 'needs_review'

        applicant.vetted_at = datetime.utcnow()
        db.session.commit()


# ============================================================================
# Flag Management
# ============================================================================

@app.route('/flags/<int:flag_id>/review', methods=['POST'])
def review_flag(flag_id):
    """Review and update a flag's status."""
    flag = Flag.query.get_or_404(flag_id)

    flag.review_status = request.form.get('review_status', flag.review_status)
    flag.review_notes = request.form.get('review_notes', flag.review_notes)
    flag.reviewed_by = request.form.get('reviewed_by', 'Manual Review')
    flag.reviewed_at = datetime.utcnow()

    db.session.commit()

    flash('Flag updated.', 'success')
    return redirect(url_for('view_applicant', applicant_id=flag.applicant_id))


# ============================================================================
# Reports
# ============================================================================

@app.route('/applicants/<int:applicant_id>/report')
def generate_report(applicant_id):
    """Generate a vetting report for an applicant."""
    applicant = Applicant.query.get_or_404(applicant_id)

    report_data = {
        'applicant': applicant.to_dict(),
        'profiles': [p.to_dict() for p in applicant.social_profiles],
        'flags': [f.to_dict() for f in applicant.flags],
        'sanctions_check': applicant.sanctions_check.to_dict() if applicant.sanctions_check else None,
        'content_summary': {
            'total_items': len(applicant.content_items),
            'by_platform': {}
        },
        'generated_at': datetime.utcnow().isoformat()
    }

    # Summarize content by platform
    for item in applicant.content_items:
        platform = item.platform
        if platform not in report_data['content_summary']['by_platform']:
            report_data['content_summary']['by_platform'][platform] = 0
        report_data['content_summary']['by_platform'][platform] += 1

    return render_template('report.html', applicant=applicant, report=report_data)


@app.route('/applicants/<int:applicant_id>/report/json')
def export_report_json(applicant_id):
    """Export vetting report as JSON."""
    applicant = Applicant.query.get_or_404(applicant_id)

    report_data = {
        'applicant': applicant.to_dict(),
        'profiles': [p.to_dict() for p in applicant.social_profiles],
        'flags': [f.to_dict() for f in applicant.flags],
        'sanctions_check': applicant.sanctions_check.to_dict() if applicant.sanctions_check else None,
        'content_items': [c.to_dict() for c in applicant.content_items],
        'generated_at': datetime.utcnow().isoformat()
    }

    return jsonify(report_data)


# ============================================================================
# API Routes
# ============================================================================

@app.route('/api/applicants', methods=['GET'])
def api_list_applicants():
    """API: List all applicants."""
    applicants = Applicant.query.all()
    return jsonify([a.to_dict() for a in applicants])


@app.route('/api/applicants', methods=['POST'])
def api_create_applicant():
    """API: Create a new applicant."""
    data = request.json

    applicant = Applicant(
        name=data.get('name'),
        email=data.get('email'),
        organization=data.get('organization'),
        country=data.get('country'),
        notes=data.get('notes'),
        status='pending'
    )
    db.session.add(applicant)
    db.session.flush()

    # Add profiles if provided
    for profile_data in data.get('profiles', []):
        profile = SocialProfile(
            applicant_id=applicant.id,
            platform=profile_data.get('platform'),
            username=profile_data.get('username'),
            url=profile_data.get('url'),
            platform_id=profile_data.get('platform_id'),
            discovery_method='provided'
        )
        db.session.add(profile)

    db.session.commit()

    return jsonify(applicant.to_dict()), 201


@app.route('/api/applicants/<int:applicant_id>', methods=['GET'])
def api_get_applicant(applicant_id):
    """API: Get applicant details."""
    applicant = Applicant.query.get_or_404(applicant_id)
    return jsonify(applicant.to_dict())


@app.route('/api/applicants/<int:applicant_id>/analyze', methods=['POST'])
def api_analyze_applicant(applicant_id):
    """API: Run analysis on an applicant."""
    applicant = Applicant.query.get_or_404(applicant_id)

    content_items = [
        {
            'text_content': item.text_content,
            'platform': item.platform,
            'url': item.url,
            'published_at': item.published_at.isoformat() if item.published_at else None
        }
        for item in applicant.content_items
        if item.text_content
    ]

    result = guidelines_analyzer.analyze_applicant(
        applicant_data={
            'id': applicant.id,
            'name': applicant.name,
            'country': applicant.country
        },
        content_items=content_items
    )

    return jsonify(result.to_dict())


@app.route('/api/analyze-text', methods=['POST'])
def api_analyze_text():
    """API: Analyze arbitrary text for guideline violations."""
    data = request.json
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    flags = guidelines_analyzer.analyze_single_content(text)

    return jsonify({
        'flags': [f.to_dict() for f in flags],
        'flags_count': len(flags)
    })


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=5000)
