from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'chatroom',
        'message_id',
        'message_content',
        'reporter',
        'reason',
        'created_at',
    )
    list_filter = ('reason', 'created_at', 'chatroom')
    search_fields = (
        'reporter__username',
        'reason',
        'description',
        'message__content',
        'chatroom__id',
    )
    readonly_fields = (
        'chatroom',
        'message',
        'reporter',
        'reason',
        'description',
        'created_at',
    )
    ordering = ('-created_at',)

    # message_id 컬럼
    def message_id(self, obj):
        return obj.message.id
    message_id.short_description = 'Message ID'

    # 메시지 내용 일부 표시
    def message_content(self, obj):
        return (obj.message.content[:50] + '...') if len(obj.message.content) > 50 else obj.message.content
    message_content.short_description = 'Message Content'

