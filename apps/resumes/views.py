from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from supabase import create_client
from .services import parse_resume, count_words, get_file_bytes

def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

class ResumeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        supabase = get_supabase_client()
        response = supabase.table('resumes').select('*').eq('user_id', request.user.username).order('created_at', desc=True).execute()
        return Response(response.data)

    def post(self, request):
        try:
            if 'file' not in request.FILES:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

            file = request.FILES['file']
            filename = file.name

            try:
                parsed_text = parse_resume(file, filename)
            except Exception as e:
                return Response({'error': f'Failed to parse file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            word_count = count_words(parsed_text)
            
            file_bytes = get_file_bytes(file)

            supabase = get_supabase_client()
            user_id = request.user.username
            file_path = f"{user_id}/{filename}"
            
            try:
                supabase.storage.from_("resume-uploads").upload(
                    path=file_path,
                    file=file_bytes,
                    file_options={"content-type": file.content_type, "upsert": "true"}
                )
            except Exception as e:
                print("Storage upload exception:", e)

            record_data = {
                "user_id": user_id,
                "filename": filename,
                "parsed_text": parsed_text,
                "file_path": file_path,
                "word_count": word_count
            }

            db_response = supabase.table('resumes').insert(record_data).execute()
            
            if len(db_response.data) > 0:
                return Response(db_response.data[0], status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Failed to insert to Supabase'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResumeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        supabase = get_supabase_client()
        response = supabase.table('resumes').select('*').eq('id', pk).eq('user_id', request.user.username).execute()
        if len(response.data) == 0:
            return Response({'error': 'Resume not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(response.data[0])

    def delete(self, request, pk):
        supabase = get_supabase_client()
        response = supabase.table('resumes').delete().eq('id', pk).eq('user_id', request.user.username).execute()
        return Response(status=status.HTTP_204_NO_CONTENT)