from dishka import Provider, Scope, provide

from brain.application.interactors import (
    AppendNoteFromDraftInteractor,
    CreateDraftInteractor,
    CreateNoteFromDraftInteractor,
    CreateNoteInteractor,
    DeleteDraftInteractor,
    DeleteNoteInteractor,
    ExportNotesInteractor,
    GetDraftCreationStatsInteractor,
    GetDraftInteractor,
    GetDraftsInteractor,
    GetFileInteractor,
    GetGraphInteractor,
    GetNewNoteTitleInteractor,
    GetNoteCreationStatsInteractor,
    GetNoteInteractor,
    GetNotesInteractor,
    GetUserInteractor,
    ImportNotesInteractor,
    MergeNotesInteractor,
    SearchDraftsByTextInteractor,
    SearchNotesByTitleInteractor,
    SearchWikilinkSuggestionsInteractor,
    UpdateDraftInteractor,
    UpdateNoteInteractor,
    UploadFileInteractor,
    UploadUserProfilePictureInteractor,
    UserInteractor,
)
from brain.application.interactors.auth.authorize_api_key import AuthorizeApiKeyInteractor
from brain.application.interactors.auth.create_api_key import CreateApiKeyInteractor
from brain.application.interactors.auth.delete_api_key import DeleteApiKeyInteractor
from brain.application.interactors.auth.get_api_keys import GetApiKeysInteractor
from brain.application.interactors.auth.interactor import AuthInteractor
from brain.application.interactors.auth.request_authorization import RequestAuthorizationInteractor
from brain.application.interactors.auth.set_user_pin import SetUserPinInteractor
from brain.application.interactors.auth.session_interactor import TelegramBotAuthSessionInteractor
from brain.application.interactors.auth.verify_user_pin import VerifyUserPinInteractor
from brain.application.interactors.users.update_all_profile_pictures import UpdateAllUsersProfilePicturesInteractor
from brain.application.services.api_key_authorization import ApiKeyAuthorizationService
from brain.application.services.auth_tokens import AuthTokensService
from brain.application.services.draft_access import DraftDeletionService, DraftLookupService
from brain.application.services.draft_hashtag_sync import DraftHashtagSyncService
from brain.application.services.keyword_notes import KeywordNoteService
from brain.application.services.note_crud import NoteCreationService, NoteDeletionService, NoteUpdateService
from brain.application.services.note_keyword_sync import NoteKeywordSyncService
from brain.application.services.note_lookup import NoteLookupService
from brain.application.services.note_titles import NoteTitleService
from brain.application.services.pin_verification import PinVerificationService
from brain.application.services.user_lookup import UserLookupService
from brain.application.services.user_profile_picture import UserProfilePictureService
from brain.domain.services.note_text import NoteTextService


class InteractorProvider(Provider):
    get_user_lookup_service = provide(UserLookupService, scope=Scope.REQUEST)
    get_user_profile_picture_service = provide(UserProfilePictureService, scope=Scope.REQUEST)
    get_auth_tokens_service = provide(AuthTokensService, scope=Scope.REQUEST)
    get_pin_verification_service = provide(PinVerificationService, scope=Scope.REQUEST)
    get_api_key_authorization_service = provide(ApiKeyAuthorizationService, scope=Scope.REQUEST)
    get_note_creation_service = provide(NoteCreationService, scope=Scope.REQUEST)
    get_note_update_service = provide(NoteUpdateService, scope=Scope.REQUEST)
    get_note_deletion_service = provide(NoteDeletionService, scope=Scope.REQUEST)
    get_note_lookup_service = provide(NoteLookupService, scope=Scope.REQUEST)
    get_draft_lookup_service = provide(DraftLookupService, scope=Scope.REQUEST)
    get_draft_deletion_service = provide(DraftDeletionService, scope=Scope.REQUEST)

    get_user_interactor = provide(UserInteractor, scope=Scope.REQUEST)
    get_get_user_interactor = provide(GetUserInteractor, scope=Scope.REQUEST)
    get_upload_user_profile_picture_interactor = provide(UploadUserProfilePictureInteractor, scope=Scope.REQUEST)
    get_upload_file_interactor = provide(UploadFileInteractor, scope=Scope.REQUEST)
    get_get_file_interactor = provide(GetFileInteractor, scope=Scope.REQUEST)
    get_update_all_users_profile_pictures_interactor = provide(
        UpdateAllUsersProfilePicturesInteractor,
        scope=Scope.REQUEST,
    )

    get_keyword_note_service = provide(KeywordNoteService, scope=Scope.REQUEST)
    get_note_title_service = provide(NoteTitleService, scope=Scope.REQUEST)
    get_draft_hashtag_sync_service = provide(DraftHashtagSyncService, scope=Scope.REQUEST)
    get_note_keyword_sync_service = provide(NoteKeywordSyncService, scope=Scope.REQUEST)
    get_note_text_service = provide(NoteTextService, scope=Scope.REQUEST)

    get_create_note_interactor = provide(CreateNoteInteractor, scope=Scope.REQUEST)
    get_create_note_from_draft_interactor = provide(CreateNoteFromDraftInteractor, scope=Scope.REQUEST)
    get_create_draft_interactor = provide(CreateDraftInteractor, scope=Scope.REQUEST)
    get_update_note_interactor = provide(UpdateNoteInteractor, scope=Scope.REQUEST)
    get_merge_notes_interactor = provide(MergeNotesInteractor, scope=Scope.REQUEST)
    get_append_note_from_draft_interactor = provide(AppendNoteFromDraftInteractor, scope=Scope.REQUEST)
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
    get_request_authorization_interactor = provide(RequestAuthorizationInteractor, scope=Scope.REQUEST)
    get_create_api_key_interactor = provide(CreateApiKeyInteractor, scope=Scope.REQUEST)
    get_get_api_keys_interactor = provide(GetApiKeysInteractor, scope=Scope.REQUEST)
    get_delete_api_key_interactor = provide(DeleteApiKeyInteractor, scope=Scope.REQUEST)
    get_authorize_api_key_interactor = provide(AuthorizeApiKeyInteractor, scope=Scope.REQUEST)
    get_telegram_bot_auth_session_interactor = provide(TelegramBotAuthSessionInteractor, scope=Scope.REQUEST)
    get_set_user_pin_interactor = provide(SetUserPinInteractor, scope=Scope.REQUEST)
    get_verify_user_pin_interactor = provide(VerifyUserPinInteractor, scope=Scope.REQUEST)

    get_export_notes_interactor = provide(ExportNotesInteractor, scope=Scope.REQUEST)
    get_import_notes_interactor = provide(ImportNotesInteractor, scope=Scope.REQUEST)
