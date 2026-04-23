from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from supabase import create_client, ClientOptions
from .tasks import run_optimization_sync


def get_supabase_client(request):
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1] if auth_header and ' ' in auth_header else ''
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
        options=ClientOptions(headers={"Authorization": f"Bearer {token}"})
    )


def _get_token(request):
    auth_header = request.headers.get('Authorization')
    return auth_header.split(' ')[1] if auth_header and ' ' in auth_header else ''


class OptimizationStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        resume_id = data.get('resume_id')
        job_description_text = data.get('job_description_text')
        target_job_title = data.get('target_job_title', '')

        if not resume_id or not job_description_text:
            return Response(
                {'error': 'resume_id and job_description_text are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        supabase = get_supabase_client(request)
        user_id = request.user.username

        resume_response = supabase.table('resumes').select('*').eq('id', resume_id).eq('user_id', user_id).execute()
        if not resume_response.data:
            return Response({'error': 'Resume not found'}, status=status.HTTP_404_NOT_FOUND)

        credits_response = supabase.table('profiles').select('credits_remaining').eq('id', user_id).execute()
        if not credits_response.data or credits_response.data[0].get('credits_remaining', 0) < 1:
            return Response(
                {'error': 'Insufficient credits'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        session_data = {
            'user_id': user_id,
            'resume_id': resume_id,
            'job_description_text': job_description_text,
            'target_job_title': target_job_title,
            'opt_add_projects': data.get('opt_add_projects', True),
            'opt_add_experience': data.get('opt_add_experience', True),
            'opt_recreate_summary': data.get('opt_recreate_summary', False),
            'status': 'pending'
        }

        session_response = supabase.table('sessions').insert(session_data).execute()
        session = session_response.data[0]

        supabase.table('profiles').update({'credits_remaining': credits_response.data[0]['credits_remaining'] - 1}).eq('id', user_id).execute()

        import threading
        # Run in background to let the user redirect to history immediately
        token = _get_token(request)
        thread = threading.Thread(
            target=run_optimization_sync,
            args=(str(session['id']), token)
        )
        thread.start()

        return Response(session, status=status.HTTP_201_CREATED)


class OptimizationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        supabase = get_supabase_client(request)
        user_id = request.user.username

        response = supabase.table('sessions').select('*').eq('id', session_id).eq('user_id', user_id).execute()

        if not response.data:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(response.data[0])


class OptimizationResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        supabase = get_supabase_client(request)
        user_id = request.user.username

        session_response = supabase.table('sessions').select('*').eq('id', session_id).eq('user_id', user_id).execute()

        if not session_response.data:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        session = session_response.data[0]

        if session['status'] != 'completed':
            return Response(
                {'error': 'Session not completed', 'status': session['status']},
                status=status.HTTP_400_BAD_REQUEST
            )

        result_response = supabase.table('optimized_results').select('*').eq('session_id', session_id).execute()

        if not result_response.data:
            return Response({'error': 'Result not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(result_response.data[0])


class OptimizationAuditView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        supabase = get_supabase_client(request)
        user_id = request.user.username

        session_response = supabase.table('sessions').select('*').eq('id', session_id).eq('user_id', user_id).execute()

        if not session_response.data:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        session = session_response.data[0]

        if session['status'] != 'completed':
            return Response({'error': 'Session not completed'}, status=status.HTTP_400_BAD_REQUEST)

        result_response = supabase.table('optimized_results').select('*').eq('session_id', session_id).execute()

        if not result_response.data:
            return Response({'error': 'Result not found'}, status=status.HTTP_404_NOT_FOUND)

        result_id = result_response.data[0]['id']
        audit_response = supabase.table('audit_trails').select('*').eq('optimized_result_id', result_id).execute()

        return Response(audit_response.data)


class OptimizationHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        supabase = get_supabase_client(request)
        user_id = request.user.username

        response = supabase.table('sessions').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()

        return Response(response.data)


class OptimizationRetryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        supabase = get_supabase_client(request)
        user_id = request.user.username

        print(f"[RETRY] Request for session: {session_id}, user: {user_id}")

        session_response = supabase.table('sessions').select('*').eq('id', str(session_id)).eq('user_id', user_id).execute()

        if not session_response.data:
            print(f"[RETRY] Session not found in Supabase for id={session_id}, user={user_id}")
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            token = _get_token(request)
            print(f"[RETRY] Starting optimization with token present: {bool(token)}")
            result = run_optimization_sync(str(session_id), token)
            print(f"[RETRY] Optimization finished: {result}")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"[RETRY] Optimization failed: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)