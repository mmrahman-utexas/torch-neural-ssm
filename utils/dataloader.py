"""
@file dataloader.py
@author Ryan Missel

Holds the LightningDataModule for the available datasets
"""
import torch
import numpy as np
import pytorch_lightning
from torch.utils.data import Dataset, DataLoader


class SSMDataset(Dataset):
    """ Basic Dataset object for the SSM """
    def __init__(self, images, labels, states, controls):
        self.images = images
        self.labels = labels
        self.states = states
        self.controls = controls

    def __len__(self):
        return self.images.shape[0]

    def __getitem__(self, idx):
        return torch.Tensor([idx]), self.images[idx], self.states[idx], self.controls[idx], self.labels[idx]


class SSMDataModule(pytorch_lightning.LightningDataModule):
    """ Custom DataModule object that handles preprocessing all sets of data for a given run """
    def __init__(self, cfg):
        super(SSMDataModule, self).__init__()
        self.cfg = cfg

    def make_loader(self, mode="train", evaluation=False, shuffle=True):
        # Load in NPZ
        npzfile = np.load(f"data/{self.cfg.dataset}/{mode}.npz")

        # Load in data sources
        images = npzfile['image'].astype(np.float32)
        labels = npzfile['label'].astype(np.int16)
        states = npzfile['state'].astype(np.float32)[:, :, :2]

        # Load control, if it exists, else make a dummy one
        controls = npzfile['control'] if 'control' in npzfile else np.zeros((images.shape[0], images.shape[1], 1), dtype=np.float32)

        # Modify based on dataset percent
        rand_idx = np.random.choice(range(images.shape[0]), size=int(images.shape[0] * self.cfg.dataset_percent), replace=False)
        images = images[rand_idx]
        labels = labels[rand_idx]
        states = states[rand_idx]
        controls = controls[rand_idx]

        # Convert to Tensors
        images = torch.from_numpy(images)
        labels = torch.from_numpy(labels)
        states = torch.from_numpy(states)
        controls = torch.from_numpy(controls)

        # Build dataset and corresponding Dataloader
        dataset = SSMDataset(images, labels, states, controls)

        # If it is the training setting, set up the iterative dataloader
        if mode == "train" and evaluation is False:
            sampler = torch.utils.data.RandomSampler(dataset, replacement=True, num_samples=self.cfg.num_steps * self.cfg.batch_size)
            dataloader = DataLoader(dataset, sampler=sampler, batch_size=self.cfg.batch_size, drop_last=True)

        # Otherwise, setup a normal dataloader
        else:
            dataloader = DataLoader(dataset, batch_size=self.cfg.batch_size, shuffle=shuffle)
        return dataloader

    def train_dataloader(self):
        """ Getter function that builds and returns the training dataloader """
        return self.make_loader("train")

    def evaluate_train_dataloader(self):
        return self.make_loader("train", evaluation=True, shuffle=False)

    def val_dataloader(self):
        """ Getter function that builds and returns the validation dataloader """
        return self.make_loader("val", shuffle=False)

    def test_dataloader(self):
        """ Getter function that builds and returns the testing dataloader """
        return self.make_loader("test", shuffle=False)
