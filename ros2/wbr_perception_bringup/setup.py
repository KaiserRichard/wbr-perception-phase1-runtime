from glob import glob
from setuptools import find_packages, setup

setup(name="wbr_perception_bringup", version="0.1.0", packages=find_packages(),
      data_files=[("share/ament_index/resource_index/packages", ["resource/wbr_perception_bringup"]),
                  ("share/wbr_perception_bringup", ["package.xml"]),
                  ("share/wbr_perception_bringup/launch", glob("launch/*.launch.py")),
                  ("share/wbr_perception_bringup/config", glob("config/*.json"))],
      install_requires=["setuptools"], zip_safe=True,
      maintainer="WBR maintainers", maintainer_email="maintainer@example.invalid",
      description="Ordered native perception stack bring-up", license="GPL-3.0-or-later",
      entry_points={"console_scripts": [
          "stack_supervisor = wbr_perception_bringup.supervisor:main"]})
