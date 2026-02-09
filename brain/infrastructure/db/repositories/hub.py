from dataclasses import dataclass

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.abstractions.repositories.hashtags import IHashtagsRepository
from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.keywords import IKeywordsRepository
from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.abstractions.repositories.s3_files import (
    IS3FilesRepository,
)


@dataclass
class RepositoryHub:
    users: IUsersRepository
    s3_files: IS3FilesRepository
    drafts: IDraftsRepository
    hashtags: IHashtagsRepository
    notes: INotesRepository
    keywords: IKeywordsRepository
