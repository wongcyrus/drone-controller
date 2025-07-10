from djitellopy import TelloSwarm, Tello


drone_hosts = ["192.168.137.21", "192.168.137.22"]  # Legacy default


# Real drone
drone1 = Tello(host=drone_hosts[0])
drone2 = Tello(host=drone_hosts[1])
drones = [drone1, drone2]

swarm = TelloSwarm(drones)

# Connect to the swarm
swarm.connect()

swarm.takeoff()
import time
# Wait for drones to stabilize
time.sleep(5)

# Print battery level for each drone in the swarm
for i, tello in enumerate(swarm.tellos):
    print(f"Drone {i+1} battery: {tello.get_battery()}%")
# Send a command to all drones in the swarm

swarm.parallel(lambda i,t: t.send_keepalive())
time.sleep(14)
print("1st 14s")

swarm.parallel(lambda i,t: t.move_up(50))
print("All drones moved up successfully")
time.sleep(14)
# for tello in swarm:
#     print(tello.send_keepalive())
swarm.parallel(lambda i,t: t.send_keepalive())

time.sleep(14)
print("2nd 14s")
print("Keepalive sent successfully")
# Land all drones in the swarm
swarm.land()
print("All drones landed successfully")



