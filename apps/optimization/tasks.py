from celery import shared_task
import os
from datetime import datetime
from supabase import create_client
from django.conf import settings


def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def run_optimization_logic(session_id: str, token: str = None):
    print(f"[TASKS] Starting optimization for session: {session_id}")
    if token:
        from supabase import ClientOptions
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
            options=ClientOptions(headers={"Authorization": f"Bearer {token}"})
        )
    else:
        supabase = get_supabase_client()
    print(f"[TASKS] Supabase client created (authenticated: {bool(token)})")
    
    session_res = supabase.table('sessions').select('*, resumes(parsed_text)').eq('id', session_id).execute()
    print(f"[TASKS] Session query result: {len(session_res.data)} records")
    
    if not session_res.data:
        raise Exception(f"Session {session_id} not found in Supabase")
    session = session_res.data[0]
    print(f"[TASKS] Session found: status={session.get('status')}")
    
    supabase.table('sessions').update({'status': 'processing'}).eq('id', session_id).execute()
    
    try:
        from .ai_service import run_optimization as ai_run
        
        resume_text = session.get('resumes', {}).get('parsed_text', '')
        print(f"[TASKS] Resume text length: {len(resume_text) if resume_text else 0}")
        
        if not resume_text:
            raise Exception("Resume text is empty or missing")
            
        jd_text = session.get('job_description_text', '')
        print(f"[TASKS] JD text length: {len(jd_text) if jd_text else 0}")
        
        print("[TASKS] Calling AI optimization...")
        rewritten_text, audit_entries = ai_run(resume_text, jd_text)
        print(f"[TASKS] AI optimization done. Result length: {len(rewritten_text)}")
        
        result_res = supabase.table('optimized_results').insert({
            'session_id': session_id,
            'rewritten_text': rewritten_text
        }).execute()
        result_id = result_res.data[0]['id']
        print(f"[TASKS] Result created: {result_id}")
        
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
        
        print("[TASKS] Optimization completed successfully")
        return {'status': 'completed', 'result_id': result_id}
        
    except Exception as e:
        print(f"[TASKS] Error during optimization: {e}")
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

