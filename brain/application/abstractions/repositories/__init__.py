from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.abstractions.repositories.keywords import IKeywordsRepository
from brain.application.abstractions.repositories.hashtags import IHashtagsRepository
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.abstractions.repositories.s3_files import (
    IS3FilesRepository,
)
from brain.application.abstractions.repositories.tg_bot_auth import (
    ITelegramBotAuthSessionsRepository,
)
from brain.application.abstractions.repositories.jwt import (
    IJwtRefreshTokensRepository,
)
from brain.application.abstractions.repositories.api_keys import (
    IApiKeysRepository,
)
