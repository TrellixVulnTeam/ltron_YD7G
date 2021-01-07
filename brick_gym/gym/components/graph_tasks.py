import brick_gym.utils as utils
import brick_gym.evaluation as evaluation
import brick_gym.gym.spaces as bg_spaces
from brick_gym.gym.components.brick_env_component import BrickEnvComponent

class GraphConstructionTask(BrickEnvComponent):
    def __init__(self,
            num_classes,
            max_nodes,
            scene_component):
        
        self.num_classes = num_classes
        self.max_nodes = max_nodes
        self.scene_component = scene_component
        
        self.action_space = bg_spaces.GraphScoreSpace(
                self.num_classes, self.max_nodes)
    
    def step(self, action):
        predicted_edge_scores = utils.matrix_to_edge_scores(
                None, action['nodes'], action['edges'])
        target_edge_scores = GET_SCENE_GRAPH
        _, _, ap = evaluation.edge_ap(
                predicted_edge_scores, target_edge_scores)
        
        return None, ap, False, None
    
    '''
    def get_predicted_edge_scores(self, action):
        predicted_edge_scores = utils.matrix_to_edge_scores(
                None, predicted_graph['nodes'], predicted_graph['edges'])
        return predicted_edge_scores
    
    def compute_reward(self, state, action):
        scene_metadata = state[self.scene_metadata_key]
        target_edge_scores = utils.metadata_to_edge_scores(
                None, scene_metadata)
        predicted_edge_scores = self.get_predicted_edge_scores(action)
        _, _, ap = evaluation.edge_ap(
                predicted_edge_scores, target_edge_scores)
        return ap
    '''

class SparseGraphConstructionTask(GraphReconstructionTask)
    def __init__(self,
            num_classes,
            max_nodes,
            max_edges,
            graph_key='graph',
            scene_metadata_key='scene_metadata'):
        
        self.max_edges = max_edges
        super(SparseGraphReconstructionTask, self).__init__(
                num_classes=num_classes,
                max_nodes=max_nodes,
                graph_key=graph_key,
                scene_metadata_key=scene_metadata_key)
    
    def update_action_space(self, action_space):
        action_space[self.graph_key] = bg_spaces.SparseGraphScoreSpace(
                self.num_classes, self.max_nodes, self.max_edges)
    
    def get_predicted_edge_scores(self, action):
        predicted_sparse_graph = action[self.graph_key]
        predicted_edge_scores = utils.sparse_graph_to_edge_scores(
                None,
                predicted_sparse_graph['nodes'],
                predicted_sparse_graph['edges'],
                predicted_sparse_graph['scores'])
        return predicted_edge_scores