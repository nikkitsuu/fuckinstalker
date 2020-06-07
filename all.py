from tests.base import SherlockBaseTest
import unittest


class SherlockDetectTests(SherlockBaseTest):
    def test_detect_true_via_message(self):

        site = 'Instructables'
        site_data = self.site_data_all[site]

        #Ensure that the site's detection method has not changed.
        self.assertEqual("message", site_data["errorType"])

        self.username_check([site_data["username_claimed"]],
                            [site],
                            exist_check=True
                           )

        return

    def test_detect_false_via_message(self):

        site = 'Instructables'
        site_data = self.site_data_all[site]

        #Ensure that the site's detection method has not changed.
        self.assertEqual("message", site_data["errorType"])

        self.username_check([site_data["username_unclaimed"]],
                            [site],
                            exist_check=False
                           )

        return

    def test_detect_true_via_status_code(self):

        site = 'Facebook'
        site_data = self.site_data_all[site]

        #Ensure that the site's detection method has not changed.
        self.assertEqual("status_code", site_data["errorType"])

        self.username_check([site_data["username_claimed"]],
                            [site],
                            exist_check=True
                           )

        return

    def test_detect_false_via_status_code(self):

        site = 'Facebook'
        site_data = self.site_data_all[site]

        #Ensure that the site's detection method has not changed.
        self.assertEqual("status_code", site_data["errorType"])

        self.username_check([site_data["username_unclaimed"]],
                            [site],
                            exist_check=False
                           )

        return

    def test_detect_true_via_response_url(self):

        site = 'Quora'
        site_data = self.site_data_all[site]

        #Ensure that the site's detection method has not changed.
        self.assertEqual("response_url", site_data["errorType"])

        self.username_check([site_data["username_claimed"]],
                            [site],
                            exist_check=True
                           )

        return

    def test_detect_false_via_response_url(self):

        site = 'Quora'
        site_data = self.site_data_all[site]

        #Ensure that the site's detection method has not changed.
        self.assertEqual("response_url", site_data["errorType"])

        self.username_check([site_data["username_unclaimed"]],
                            [site],
                            exist_check=False
                           )

        return


class SherlockSiteCoverageTests(SherlockBaseTest):
    def test_coverage_false_via_response_url(self):

        self.detect_type_check("response_url", exist_check=False)

        return

    def test_coverage_true_via_response_url(self):

        self.detect_type_check("response_url", exist_check=True)

        return

    def test_coverage_false_via_status(self):

        self.detect_type_check("status_code", exist_check=False)

        return

    def test_coverage_true_via_status(self):

        self.detect_type_check("status_code", exist_check=True)

        return

    def test_coverage_false_via_message(self):

        self.detect_type_check("message", exist_check=False)

        return

    def test_coverage_true_via_message(self):

        self.detect_type_check("message", exist_check=True)

        return

    def test_coverage_total(self):

        self.coverage_total_check()

        return
