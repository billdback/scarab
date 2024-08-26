# Temporarily putting the beehive here until I can split out the projects into multiple projects.
# beehive will be the initial test project anyway, so put it here.
from scarab.examples.beehive.bee import BasicBee
from scarab.examples.beehive.hive import Hive

# bee = BasicBee(True, False)
# print(bee)

hive = Hive()
hive.bee_created(BasicBee())
print(hive)

# temp = DailyTemperature(max_temp=25.0, min_temp=0.0)
# print(temp)



