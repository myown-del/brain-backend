from uuid import UUID

from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.interactors.users.exceptions import UserNotFoundException
from brain.application.services.pin_verification import PinVerificationService


class VerifyUserPinInteractor:
    def __init__(
        self,
        users_repo: IUsersRepository,
        pin_verification_service: PinVerificationService,
    ):
        self._users_repo = users_repo
        self._pin_verification_service = pin_verification_service

    async def verify_pin(self, user_id: UUID, pin: str) -> bool:
        user = await self._users_repo.get_by_id(entity_id=user_id)
        if not user:
            raise UserNotFoundException()
        return self._pin_verification_service.verify_pin(
            pin=pin,
            stored_hash=user.pin_hash,
        )
