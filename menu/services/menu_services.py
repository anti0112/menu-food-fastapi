from fastapi import HTTPException

from menu.db.models import Menu
from menu.services import ServiceMixin


class MenuService(ServiceMixin):
    async def get_detail(self, menu_id: int):
        cached_menu = await self.redis_cache.get_data(f"menu:{menu_id}")

        if cached_menu:
            return cached_menu

        menu = await self.dao.menu.menu_info(menu_id=menu_id)

        if not menu:
            raise HTTPException(status_code=404, detail="menu not found")

        response_data = self.calculate_menu(menu)
        await self.redis_cache.save(f"menu:{menu_id}", response_data)

        return response_data

    async def get_list(self):
        cached_menus = await self.redis_cache.get_data("menus")

        if cached_menus:
            return cached_menus

        menus = await self.dao.menu.get_all_menus()

        result_menu = list()

        for menu in menus:
            submenus_count = len(menu.sub_menus)
            dishes_count = sum(
                len(submenu.dishes) for submenu in menu.sub_menus
            )

            menu.submenus_count = submenus_count
            menu.dishes_count = dishes_count

            result_menu.append(menu)

        await self.redis_cache.save("menus", result_menu)

        return result_menu

    async def create(self, title: str, description: str):
        menu = await self.dao.menu.create_menu(title=title, desc=description)

        menu_data = self.calculate_menu(menu)
        await self.redis_cache.clear("menus")

        return menu_data

    async def update(self, menu_id: int, **kwargs):
        menu = await self.dao.menu.menu_info(menu_id=menu_id)

        if not menu:
            raise HTTPException(status_code=404, detail="menu not found")

        menu = await self.dao.menu.update_menu(menu_id, **kwargs)

        updated_menu = self.calculate_menu(menu)
        await self.redis_cache.save(f"menu:{menu.id}", updated_menu)
        await self.redis_cache.clear("menus")

        return updated_menu

    async def delete(self, menu_id: int):
        menu = await self.dao.menu.menu_info(menu_id=menu_id)

        if not menu:
            raise HTTPException(status_code=404, detail="menu not found")

        await self.dao.menu.delete_menu(menu_id=menu_id)
        await self.redis_cache.clear(f"menu:{menu.id}", "menus")

        return True

    @staticmethod
    def calculate_menu(menu: Menu):
        submenus_count = len(menu.sub_menus)
        dishes_count = sum(len(submenu.dishes) for submenu in menu.sub_menus)

        menu.submenus_count = submenus_count
        menu.dishes_count = dishes_count

        return menu
