from dishka import Provider, Scope, provide

from brain.application.interactors import (
    CreateNoteInteractor,
    CreateNoteFromDraftInteractor,
    DeleteNoteInteractor,
    CreateDraftInteractor,
    DeleteDraftInteractor,
    GetDraftInteractor,
    GetDraftsInteractor,
    GetDraftCreationStatsInteractor,
    SearchDraftsByTextInteractor,
    UpdateDraftInteractor,
    GetGraphInteractor,
    GetUserInteractor,
    GetNoteInteractor,
    GetNewNoteTitleInteractor,
    GetNotesInteractor,
    GetNoteCreationStatsInteractor,
    SearchNotesByTitleInteractor,
    SearchWikilinkSuggestionsInteractor,
    UpdateNoteInteractor,
    UserInteractor,
    ExportNotesInteractor,
    ImportNotesInteractor,
    UploadUserProfilePictureInteractor,
    UploadFileInteractor,
)
from brain.application.interactors.users.update_all_profile_pictures import (
    UpdateAllUsersProfilePicturesInteractor,
)
from brain.application.services.draft_hashtag_sync import DraftHashtagSyncService
from brain.application.services.keyword_notes import KeywordNoteService
from brain.application.services.note_titles import NoteTitleService
from brain.application.services.note_keyword_sync import NoteKeywordSyncService
from brain.application.interactors.auth.interactor import AuthInteractor
from brain.application.interactors.auth.create_api_key import CreateApiKeyInteractor
from brain.application.interactors.auth.delete_api_key import DeleteApiKeyInteractor
from brain.application.interactors.auth.get_api_keys import GetApiKeysInteractor
from brain.application.interactors.auth.authorize_api_key import AuthorizeApiKeyInteractor
from brain.application.orchestrators.authorization import AuthorizationOrchestrator
from brain.application.interactors.auth.session_interactor import (
    TelegramBotAuthSessionInteractor,
)


class InteractorProvider(Provider):
    get_user_interactor = provide(UserInteractor, scope=Scope.REQUEST)
    get_get_user_interactor = provide(GetUserInteractor, scope=Scope.REQUEST)
    get_upload_user_profile_picture_interactor = provide(UploadUserProfilePictureInteractor, scope=Scope.REQUEST)
    get_upload_file_interactor = provide(UploadFileInteractor, scope=Scope.REQUEST)
    get_update_all_users_profile_pictures_interactor = provide(
        UpdateAllUsersProfilePicturesInteractor, scope=Scope.REQUEST
    )
    get_keyword_note_service = provide(KeywordNoteService, scope=Scope.REQUEST)
    get_note_title_service = provide(NoteTitleService, scope=Scope.REQUEST)
    get_draft_hashtag_sync_service = provide(DraftHashtagSyncService, scope=Scope.REQUEST)
    get_note_keyword_sync_service = provide(NoteKeywordSyncService, scope=Scope.REQUEST)
    get_create_note_interactor = provide(CreateNoteInteractor, scope=Scope.REQUEST)
    get_create_note_from_draft_interactor = provide(CreateNoteFromDraftInteractor, scope=Scope.REQUEST)
    get_create_draft_interactor = provide(CreateDraftInteractor, scope=Scope.REQUEST)
    get_update_note_interactor = provide(UpdateNoteInteractor, scope=Scope.REQUEST)
    get_update_draft_interactor = provide(UpdateDraftInteractor, scope=Scope.REQUEST)
    get_delete_note_interactor = provide(DeleteNoteInteractor, scope=Scope.REQUEST)
    get_delete_draft_interactor = provide(DeleteDraftInteractor, scope=Scope.REQUEST)
    get_get_notes_interactor = provide(GetNotesInteractor, scope=Scope.REQUEST)
    get_get_drafts_interactor = provide(GetDraftsInteractor, scope=Scope.REQUEST)
    get_get_draft_creation_stats_interactor = provide(GetDraftCreationStatsInteractor, scope=Scope.REQUEST)
    get_get_note_creation_stats_interactor = provide(GetNoteCreationStatsInteractor, scope=Scope.REQUEST)
    get_get_note_interactor = provide(GetNoteInteractor, scope=Scope.REQUEST)
    get_get_draft_interactor = provide(GetDraftInteractor, scope=Scope.REQUEST)
    get_get_new_note_title_interactor = provide(GetNewNoteTitleInteractor, scope=Scope.REQUEST)
    get_search_notes_by_title_interactor = provide(SearchNotesByTitleInteractor, scope=Scope.REQUEST)
    get_search_drafts_by_text_interactor = provide(SearchDraftsByTextInteractor, scope=Scope.REQUEST)
    get_search_wikilink_suggestions_interactor = provide(SearchWikilinkSuggestionsInteractor, scope=Scope.REQUEST)
    get_get_graph_interactor = provide(GetGraphInteractor, scope=Scope.REQUEST)
    get_auth_interactor = provide(AuthInteractor, scope=Scope.REQUEST)
    get_create_api_key_interactor = provide(CreateApiKeyInteractor, scope=Scope.REQUEST)
    get_get_api_keys_interactor = provide(GetApiKeysInteractor, scope=Scope.REQUEST)
    get_delete_api_key_interactor = provide(DeleteApiKeyInteractor, scope=Scope.REQUEST)
    get_authorize_api_key_interactor = provide(AuthorizeApiKeyInteractor, scope=Scope.REQUEST)
    get_authorization_orchestrator = provide(AuthorizationOrchestrator, scope=Scope.REQUEST)
    get_telegram_bot_auth_session_interactor = provide(TelegramBotAuthSessionInteractor, scope=Scope.REQUEST)
    get_export_notes_interactor = provide(ExportNotesInteractor, scope=Scope.REQUEST)
    get_import_notes_interactor = provide(ImportNotesInteractor, scope=Scope.REQUEST)
