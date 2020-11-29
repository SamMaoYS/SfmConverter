import os
import json
import numpy as np
import argparse

"""
README

Generate camera sfm file!

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input camera sfm file
  -t TRAJECTORY, --trajectory TRAJECTORY
                        Input camera trajectory file
  -m MODE, --mode MODE  mode 0: input cameraInit.sfm genereate poses for all views. 
                        mode 1: input cameras.sfm from SfM node, generate poses for
                                pose exists in cameras.sfm only.
  -o OUTPUT, --output OUTPUT
                        Output camera sfm file
"""

"""
my code structure
- main folder/
    - data/ (store cameraInit.sfm cameras.sfm bedroom.jsonl(my camera poses))
    - main.py

mode 0
command 1: python main.py -i data/cameraInit.sfm -t data/bedroom.jsonl -o data/cameraInit_new.sfm

mode 1
command 2: python main.py -i data/cameras.sfm -t data/bedroom.jsonl -m 1 -o data/cameras_new.sfm 
"""

def main(args):
    input = args.input

    with open(input) as f:
        sfm = json.load(f)
        views = sfm['views']
    if args.mode == 1:
        poses = sfm['poses']

    sfm.pop('featuresFolders', None)
    sfm.pop('matchesFolders', None)

    # the raw color image extracted from video with ffmpeg has step size 10
    # so 1 of 10 images are extracted
    step = 10
    trajectory = []
    with open(args.trajectory) as f:
        for i, line in enumerate(f):
            if i % step == 0:
                cam_info = json.loads(line)
                trans = cam_info.get('transform', None)
                trans = np.asarray(trans)
                trans = trans.reshape(4, 4).transpose()

                # camera coordinates transform
                trans = np.matmul(trans, np.diag([1, -1, -1, 1]))
                trans = trans/trans[3][3]
                trajectory.append(trans)
    
    print(f'there are {len(trajectory)} camera poses in trajectory')
    # sfm['intrinsics'][0]['locked'] = "1"

    if args.mode == 0:
        poses = []

    count = 0
    for view in views:
        pose_id = view['poseId']
        img_id = os.path.basename(os.path.splitext(view['path'])[0])
        rotation = trajectory[int(img_id)][0:3, 0:3].transpose().flatten().astype('str').tolist()
        # center: R.transpose()*(-translate)
        center = np.matmul(trajectory[int(img_id)][0:3, 0:3].transpose(), -trajectory[int(img_id)][0:3, 3]).astype('str').tolist()
        # input cameraInit.sfm from camera init node, add all camera poses for all views
        if args.mode == 0:
            pose = {"poseId": pose_id, 'pose': {}}
            pose['pose']['transform']={}
            pose['pose']['transform']['rotation'] = rotation
            pose['pose']['transform']['center'] = center
            pose['pose']['locked'] = "1"
            poses.append(pose)
            count += 1
        # input cameras.sfm from SfM node, replace geneated poses
        elif args.mode == 1:
            for pose in poses:
                if pose['poseId'] == pose_id:
                    pose['pose']['transform']['rotation'] = rotation
                    pose['pose']['transform']['center'] = center
                    pose['pose']['locked'] = "1"
                    count += 1

    sfm['poses'] = poses
    print(f'{len(views)} of views in total')
    print(f'{len(poses)} of poses in total')
    print(f'{count} of poses are replaces')

    with open(args.output, 'w+') as f:
        json.dump(sfm, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate camera sfm file!')
    parser.add_argument('-i', '--input', dest='input', type=str, action='store', required=True,
                        help='Input camera sfm file')
    parser.add_argument('-t', '--trajectory', dest='trajectory', default='data/bedroom.jsonl', type=str, action='store', required=False,
                        help='Input camera trajectory file')
    parser.add_argument('-m', '--mode', dest='mode', type=int, default=0, action='store', required=False,
                        help='mode 0: input cameraInit.sfm genereate poses for all views.\n \
                            mode 1: input cameras.sfm from SfM node, generate poses for pose exists in cameras.sfm only.')
    parser.add_argument('-o', '--output', dest='output', default='cameras_new.sfm', type=str, action='store', required=False,
                        help='Output camera sfm file')

    args = parser.parse_args()

    main(args)