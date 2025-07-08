#!/usr/bin/env python3
"""
SEO Implementation Validation Script
Tests that SEO context processors and route SEO data are working correctly
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/viktorigesund/Documents/teoritest')

def test_seo_context_processor():
    """Test that the SEO context processor is generating data correctly"""
    try:
        from app.utils.seo_context import inject_seo_context
        from app.utils.seo import SEOGenerator, SEOPageConfigs
        print("✅ Successfully imported SEO modules")
        
        # Test homepage config
        config = SEOPageConfigs.homepage()
        print(f"✅ Homepage config: {config['title']}")
        
        # Test quiz config
        quiz_config = SEOPageConfigs.quiz_page('Trafikkskilt')
        print(f"✅ Quiz config: {quiz_config['title']}")
        
        # Test breadcrumb generation
        breadcrumbs = [('Hjem', '/'), ('Quiz', '/quiz'), ('Trafikkskilt', '/quiz?category=Trafikkskilt')]
        breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumbs)
        print(f"✅ Breadcrumb data generated: {len(breadcrumb_data)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Error testing SEO context processor: {e}")
        return False

def test_structured_data():
    """Test structured data generation"""
    try:
        from app.utils.seo import SEOGenerator
        
        # Test website schema
        website_schema = SEOGenerator.generate_structured_data('WebSite')
        print(f"✅ Website schema generated: {len(website_schema)} characters")
        
        # Test quiz schema
        quiz_schema = SEOGenerator.generate_structured_data(
            'Quiz', 
            {'name': 'Trafikkskilt Quiz', 'description': 'Test din kunnskap om trafikkskilt'}
        )
        print(f"✅ Quiz schema generated: {len(quiz_schema)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Error testing structured data: {e}")
        return False

def test_meta_tags():
    """Test meta tag generation"""
    try:
        from app.utils.seo import SEOGenerator
        
        meta_tags = SEOGenerator.generate_meta_tags(
            title='Test Page - Sertifikatet',
            description='This is a test page for SEO validation',
            keywords='test, seo, validation',
            page_type='website'
        )
        
        required_tags = ['title', 'description', 'og_title', 'og_description', 'twitter_title']
        for tag in required_tags:
            if tag not in meta_tags:
                print(f"❌ Missing meta tag: {tag}")
                return False
        
        print(f"✅ Meta tags generated with {len(meta_tags)} fields")
        print(f"   Title: {meta_tags['title']}")
        print(f"   Description: {meta_tags['description'][:60]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error testing meta tags: {e}")
        return False

def test_norwegian_keywords():
    """Test Norwegian keyword optimization"""
    try:
        from app.utils.local_seo import LocalSEO
        
        keywords = LocalSEO.NORWEGIAN_KEYWORDS
        print(f"✅ Norwegian keywords loaded: {len(keywords)} keywords")
        
        cities = LocalSEO.NORWEGIAN_CITIES
        print(f"✅ Norwegian cities loaded: {len(cities)} cities")
        
        # Test local content meta
        local_meta = LocalSEO.generate_local_content_meta()
        print(f"✅ Local meta generated: {local_meta['geo_country']}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing Norwegian optimization: {e}")
        return False

def test_sitemap_generation():
    """Test sitemap functionality"""
    try:
        from app.utils.sitemap import SitemapGenerator
        
        # This would need a Flask app context in real testing
        print("✅ Sitemap module imported successfully")
        print("ℹ️  Sitemap generation requires Flask app context for full testing")
        
        return True
    except Exception as e:
        print(f"❌ Error testing sitemap: {e}")
        return False

def main():
    """Run all SEO validation tests"""
    print("🔍 Starting SEO Implementation Validation")
    print("=" * 50)
    
    tests = [
        ("SEO Context Processor", test_seo_context_processor),
        ("Structured Data", test_structured_data),
        ("Meta Tags", test_meta_tags),
        ("Norwegian Keywords", test_norwegian_keywords),
        ("Sitemap Generation", test_sitemap_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All SEO implementations are working correctly!")
        return True
    else:
        print("⚠️  Some SEO implementations need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
