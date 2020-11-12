"""
name: Simon HEPPNER
email: simon@heppner.at.
website: http://github.com/spheppner/sprl
license: gpl, see http://www.gnu.org/licenses/gpl-3.0.de.html
description: universal easy-to-use agent classes, made for usage in minigames
"""

import random
import numpy as np
from keras.models import Sequential, load_model
from keras.layers import Dense, LSTM
from sklearn.preprocessing import OneHotEncoder
import io


class Agent:
    """agent template"""

    def __init__(
        self, actions, rewards=[1, -1]
    ):  # format: actions=[int(action1),int(action2),...], rewards=[int(reward),int(penalty)]
        self.actions = actions
        self.rewards = rewards

    def train(
        self, X_train, Y_train
    ):  # format: X_train=[list(features1),list(features2),...], Y_train = [int(label1),int(label2),...]
        pass

    def passround(self, state):
        pass


class NaiveAgent(Agent):
    """naive agent: acts randomly"""

    def train(self, **kwargs):
        print("This Agent is not trainable.")

    def passround(self, **kwargs):
        return random.choice(self.actions)


class TrainedAgent(Agent):
    """trained agent: predicts action after training"""

    def create_model(self, xlength):
        model = Sequential()

        model.add(Dense(12, input_dim=xlength, activation="relu"))
        model.add(Dense(9, activation="relu"))
        model.add(Dense(9, activation="relu"))
        model.add(Dense(1, activation="sigmoid"))

        model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
        )
        return model

    def train(self, X_train, Y_train, savemodel=False):
        # train agent with X and Y from dataset
        xlength = len(X_train[0])

        self.model = self.create_model(xlength)
        self.model.fit(X_train, Y_train, epochs=150, batch_size=10)
        self.model.summary()
        if savemodel:
            self.model.save("model.h5")
        _, accuracy = self.model.evaluate(X_train, Y_train)
        print("Accuracy: %.2f" % (accuracy * 100))

    def loadmodel(self, model):
        self.model = model
        #self.model.summary()

    def passround(self, state):
        # predict Y | X = state
        # return Y
        predictions = self.model.predict(state)
        preds = []
        for line in predictions:
            preds.append(np.where(line == max(line))[0][0])
        return preds

class EvolvedAgent(Agent):
    """trained agent: predicts action after training"""

    def create_model(self, xlength):
        model = Sequential()

        model.add(Dense(8, input_dim=xlength, activation = "relu", kernel_initializer="he_uniform"))
        model.add(Dense(16, activation="relu", kernel_initializer='he_uniform'))
        model.add(Dense(32, activation="relu", kernel_initializer='he_uniform'))
        model.add(Dense(16, activation="relu", kernel_initializer='he_uniform'))
        model.add(Dense(32, activation="relu", kernel_initializer='he_uniform'))
        model.add(Dense(8, activation="relu", kernel_initializer='he_uniform'))
        model.add(Dense(1, activation="linear"))

        model.compile(
            optimizer="adam", loss="mean_absolute_error", metrics=["accuracy"]
        )
        return model

    def train(self, X_train, Y_train, savemodel=False):
        # train agent with X and Y from dataset
        xlength = len(X_train[0])

        self.model = self.create_model(xlength)
        self.model.fit(X_train, Y_train, epochs=150, batch_size=10)
        self.model.summary()
        if savemodel:
            self.model.save("movingmodel.h5")
        _, accuracy = self.model.evaluate(X_train, Y_train)
        print("Accuracy: %.2f" % (accuracy * 100))

    def loadmodel(self, model):
        self.model = model
        #self.model.summary()

    def passround(self, state):
        # predict Y | X = state
        # return Y
        predictions = self.model.predict(state)
        preds = []
        for line in predictions:
            preds.append(np.where(line == max(line))[0][0])
        return preds


def one_hot(encode):
    o = OneHotEncoder(sparse=False)
    return o.fit_transform(encode)


def convertstr_to_state(unmodded_string):
    state = np.array([unmodded_string.split(",")], dtype=np.float32)
    return state


def loaddataset(dataset, xlength):
    loadedtxt = np.loadtxt(dataset, delimiter=",")
    X = loadedtxt[:, 0:xlength]
    Y = loadedtxt[:, xlength]
    #Y = one_hot(Y.reshape(len(Y), 1))
    return X, Y


if __name__ == "__main__":
    # example for a naive agent with 3 different actions and reward as well as penalty:
    # agent = NaiveAgent(actions=[0, 1, 2], rewards=[1, -1])
    # agent.train()
    # action = agent.passround()  # -> returns chosen actions out of action list
    # print(action)  # -> print out chosen action

    # example for a trained agent with 4 different actions and no rewards:
    trained_agent = TrainedAgent(actions=[0, 1, 2, 3])

    # ----- loading the dataset
    # X, Y = loaddataset("dataset.txt", 9)
    # ----- actually training the agent (and saving the model)
    # trained_agent.train(X, Y, savemodel=True)

    # ----- loading a saved model -> MUCH MUCH QUICKER
    model = load_model("model.h5")
    trained_agent.loadmodel(model)
    action = trained_agent.passround(convertstr_to_state("0,1,1,0,0,1,1,1,1"))
    print(action)

    # --- TESTING -------------
    # --- pacman example ------
    # actions = [go_up, go_down, go_left, go_right]
    # state = 3x3 field around player
    # no rewards -> training
