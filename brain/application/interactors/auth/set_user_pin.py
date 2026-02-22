from uuid import UUID

from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.interactors.users.exceptions import UserNotFoundException
from brain.application.services.pin_verification import PinVerificationService


class SetUserPinInteractor:
    def __init__(
        self,
        users_repo: IUsersRepository,
        pin_verification_service: PinVerificationService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._users_repo = users_repo
        self._pin_verification_service = pin_verification_service
        self._uow_factory = uow_factory

    async def set_pin(self, user_id: UUID, pin: str) -> None:
        async with self._uow_factory() as uow:
            user = await self._users_repo.get_by_id(entity_id=user_id)
            if not user:
                raise UserNotFoundException()

            user.pin_hash = self._pin_verification_service.hash_pin(pin)
            await self._users_repo.update(entity=user)
            await uow.commit()
