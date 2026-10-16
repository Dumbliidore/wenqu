import string

from django.core import mail
from django.core.paginator import Paginator
from django.test import RequestFactory, TestCase
from users.models import EmailVerifyRecord
from utils.email_send import random_str, send_register_email
from utils.pagination import paginate
from utils.templatetags.pagination_tags import page_numbers, page_url


class PaginateTests(TestCase):
    def get_page(self, total, query_string, per_page=3):
        request = RequestFactory().get(f"/?{query_string}")
        return paginate(request, list(range(1, total + 1)), per_page)

    def test_missing_page_defaults_to_first(self):
        page = self.get_page(7, "")
        self.assertEqual(page.number, 1)
        self.assertEqual(list(page.object_list), [1, 2, 3])

    def test_uses_requested_page(self):
        page = self.get_page(7, "page=3")
        self.assertEqual(page.number, 3)
        self.assertEqual(list(page.object_list), [7])

    def test_non_integer_page_falls_back_to_first(self):
        self.assertEqual(self.get_page(7, "page=abc").number, 1)

    def test_page_beyond_range_falls_back_to_last(self):
        page = self.get_page(7, "page=99")
        self.assertEqual(page.number, 3)

    def test_empty_result_returns_empty_first_page(self):
        page = self.get_page(0, "page=5")
        self.assertEqual(page.number, 1)
        self.assertEqual(list(page.object_list), [])


class PageNumbersTests(TestCase):
    def get_page(self, pages, current, per_page=2):
        request = RequestFactory().get(f"/?page={current}")
        return paginate(request, list(range(1, pages * per_page + 1)), per_page)

    def test_short_range_lists_every_page(self):
        self.assertEqual(list(page_numbers(self.get_page(3, 1))), [1, 2, 3])

    def test_long_range_inserts_ellipsis(self):
        page = self.get_page(10, 10)
        self.assertEqual(
            list(page_numbers(page)),
            [1, Paginator.ELLIPSIS, 7, 8, 9, 10],
        )


class PageUrlTests(TestCase):
    def test_keeps_other_query_params(self):
        request = RequestFactory().get("/?sort=hot&page=2")
        self.assertEqual(page_url({"request": request}, 5), "sort=hot&page=5")

    def test_without_request_returns_empty(self):
        self.assertEqual(page_url({}, 5), "")


class EmailSendTests(TestCase):
    def test_register_email_links_to_activation_code(self):
        send_register_email("new@example.com", "register")

        record = EmailVerifyRecord.objects.get(send_type="register")
        self.assertEqual(len(record.code), 16)
        self.assertEqual(mail.outbox[0].to, ["new@example.com"])
        self.assertIn(f"/active/{record.code}", mail.outbox[0].body)

    def test_forget_email_links_to_reset_page(self):
        send_register_email("new@example.com", "forget")

        record = EmailVerifyRecord.objects.get(send_type="forget")
        self.assertEqual(len(record.code), 16)
        self.assertEqual(mail.outbox[0].to, ["new@example.com"])
        self.assertIn(f"/reset/{record.code}", mail.outbox[0].body)

    def test_update_email_code_is_four_chars(self):
        send_register_email("new@example.com", "update_email")

        record = EmailVerifyRecord.objects.get(send_type="update_email")
        self.assertEqual(len(record.code), 4)
        self.assertIn(record.code, mail.outbox[0].body)

    def test_unknown_send_type_is_rejected(self):
        with self.assertRaises(ValueError):
            send_register_email("new@example.com", "unknown")

        # 拒绝之前不能先把验证码落库，否则会留下一条永远用不上的记录
        self.assertEqual(EmailVerifyRecord.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_random_str_only_uses_alphanumeric(self):
        code = random_str(12)
        self.assertEqual(len(code), 12)
        self.assertTrue(set(code) <= set(string.ascii_letters + string.digits))
