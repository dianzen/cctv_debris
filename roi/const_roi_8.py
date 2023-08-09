# setup for idcam 18

# setting area for counting
draw_area = True
area_bawah = [(0,440), (0,380), (315,380), (315, 440), (0,440)]
area_atas = [(0,320), (0,280), (315,280), (315, 320), (0,320)]


pedestrian = False
motorcycle = False
stuck = True
stuck_time = 180                        # detik

# 1 = flow dari atas ke bawah
# 2 = flow dari bawah ke atas
direction = 2
contraflow = True

speed_recognition = True
area_distance = 15                      # meter
traffic_jam = True
traffic_jam_count = 15                  # jumlah kendaraan sehingga disebut antrean
other_objects = False
vehicle_counting = False