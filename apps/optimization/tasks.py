from celery import shared_task
import os
from datetime import datetime
from supabase import create_client
from django.conf import settings


def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def run_optimization_logic(session_id: str, token: str = None):
    if token:
        from supabase import ClientOptions
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
            options=ClientOptions(headers={"Authorization": f"Bearer {token}"})
        )
    else:
        supabase = get_supabase_client()
    
    session_res = supabase.table('sessions').select('*, resumes(parsed_text)').eq('id', session_id).execute()
    
    if not session_res.data:
        raise Exception(f"Session {session_id} not found in Supabase")
    session = session_res.data[0]
    
    supabase.table('sessions').update({'status': 'processing'}).eq('id', session_id).execute()
    
    try:
        from .ai_service import run_optimization as ai_run
        
        resume_text = session.get('resumes', {}).get('parsed_text', '')
        
        if not resume_text:
            raise Exception("Resume text is empty or missing")
            
        jd_text = session.get('job_description_text', '')
        
        # Optimization preferences
        opt_add_projects = session.get('opt_add_projects', True)
        opt_add_experience = session.get('opt_add_experience', True)
        opt_recreate_summary = session.get('opt_recreate_summary', False)
        
        rewritten_text, audit_entries = ai_run(
            resume_text, 
            jd_text,
            opt_add_projects=opt_add_projects,
            opt_add_experience=opt_add_experience,
            opt_recreate_summary=opt_recreate_summary
        )
        
        result_res = supabase.table('optimized_results').insert({
            'session_id': session_id,
            'rewritten_text': rewritten_text
        }).execute()
        result_id = result_res.data[0]['id']
        
        for entry in audit_entries:
            supabase.table('audit_trails').insert({
                'optimized_result_id': result_id,
                'original_sentence': entry.get('original_sentence', ''),
                'optimized_sentence': entry.get('optimized_sentence', ''),
                'is_honest': entry.get('is_honest', True),
                'confidence_score': entry.get('confidence_score')
            }).execute()
        

            
        supabase.table('sessions').update({
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }).eq('id', session_id).execute()
        
        return {'status': 'completed', 'result_id': result_id}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        supabase.table('sessions').update({
            'status': 'failed',
            'error_message': str(e)
        }).eq('id', session_id).execute()
        raise


@shared_task(bind=True)
def run_optimization(self, session_id: str):
    return run_optimization_logic(session_id)


# Alias for views.py import
run_optimization_sync = run_optimization_logic

