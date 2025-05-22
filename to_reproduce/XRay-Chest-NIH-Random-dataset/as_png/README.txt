Here you should store example X-rays as .png from the Random version of NIH Chest X-Ray (https://www.kaggle.com/datasets/nih-chest-xrays/sample).

In my case - for demo purpose -, I included:
1- Series Studies of 4 Patients covering most of the labels (including No Finding either at the beginning of the series or end).
2- Collections of images for each label with counts represented as:
> Atelectasis : N = 67
> Cardiomegaly : N = 72
> Consolidation : N = 82
> Edema : N = 51
> Effusion : N = 50
> Emphysema : N = 56
> Fibrosis : N = 59
> Hernia : N = 13
> Infiltration : N = 60
> Mass : N = 83
> Nodule : N = 90
> Pleural_Thickening : N = 99
> Pneumonia : N = 21
> Pneumothorax : N = 59

3- No-Finding label entries have been REMOVED except for ones included in series. This is since there is no need for them according to the logic of the app.
